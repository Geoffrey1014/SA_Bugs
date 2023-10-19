#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "cfe_branch_visitor.hpp"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::OptionCategory StubCountCategory("Stub count transformer");

const std::string DEFAULT_LIFT_STUB_ASSIGN_VAR_PREFIX = "_global_assign_var_";

static llvm::cl::list<int> NonStubUpdateList("update-non-assign-stub",
                                             llvm::cl::desc("value to each non-assign stub, format: 0,1,2"),
                                             llvm::cl::CommaSeparated, llvm::cl::ZeroOrMore);

static llvm::cl::list<int> VarStubUpdateList("update-var-assign-stub",
                                             llvm::cl::desc("value to each var-assign stub, format: 0,1,2"),
                                             llvm::cl::CommaSeparated, llvm::cl::ZeroOrMore);

static llvm::cl::opt<bool> LiftStubAssignVar("lift-stub-assign-var",
                                             llvm::cl::init(false),
                                             llvm::cl::desc("if to lift var-assign to global level, "
                                                            "cannot use with update-stub parameters"));

static llvm::cl::opt<std::string> LiftStubAssignVarPrefix("lift-stub-assign-var-prefix",
                                                          llvm::cl::init(DEFAULT_LIFT_STUB_ASSIGN_VAR_PREFIX),
                                                          llvm::cl::desc("prefix when lifting var-assign "));

class StubCountTransformer : public clang::ASTConsumer,
                             public clang::RecursiveASTVisitor<StubCountTransformer> {
    CfeRewriter R;

    using non_assign_stub_type = std::string;
    using var_assign_stub_type = std::pair<std::string, std::string>;

    FunctionDecl *MainDecl = nullptr;

    // only for non-assign stubs, e.g. `while (__VERIFIER_nondet_int()) stmt;`
    std::vector<std::string> non_assign_stubs;

    // only for assign stmt such as `int a = __VERIFIER_nondet_int();`,
    // to add condition in final error label
    std::vector<std::pair<std::string, std::string>> var_assign_stubs;

    /// return true if need to return in caller
    bool handle_rewrite_nondet(CallExpr *Call, const std::string &replacement, bool &return_value) {
        if (!rewrite_nondet_value(Call, R, replacement))
            return !(return_value = false);
        return false;
    }

    template<typename T>
    bool handle_rewrite_nondet(CallExpr *Call,
                               std::vector<T> &stub_list,
                               llvm::cl::list<int> &value_list,
                               bool &return_value) {
        unsigned int current_stub_index = stub_list.size();
        if (current_stub_index < value_list.size())
            return handle_rewrite_nondet(Call, to_str(value_list[current_stub_index]), return_value);
        return false;
    }

    /// return true if need to return in caller
    bool handle_assign_nondet(
            Expr *expr,
            std::string var_name,
            bool &return_value
    ) {
        if (auto Call = dyn_cast<CallExpr>(expr)) {
            StringRef stub_type;
            if (is_nondet_value(Call, &stub_type)) {
                if (LiftStubAssignVar.getValue()) {
                    // insert global value and replace with it
                    var_name = LiftStubAssignVarPrefix.getValue() + to_str(var_assign_stubs.size() + 1);
                    R.InsertVarDeclAtBegin("int", var_name, "0");
                    if (handle_rewrite_nondet(Call, var_name, return_value))
                        return true;
                } else if (handle_rewrite_nondet(Call, var_assign_stubs, VarStubUpdateList, return_value))
                    return true;
                var_assign_stubs.emplace_back(std::pair<std::string, std::string>(
                        var_name,
                        stub_type.str()
                ));
                /* return here, so no `TraverseCallExpr` on child nodes */
                return_value = true;
                return true;
            }
        }
        return false;
    }

public:
    void HandleTranslationUnit(ASTContext &Ctx) override {
        R.setSourceMgr(Ctx.getSourceManager(), Ctx.getLangOpts());
        if (RecursiveASTVisitor::TraverseDecl(Ctx.getTranslationUnitDecl())) {
            if (NonStubUpdateList.empty() && VarStubUpdateList.empty()) {
                // do not replace
                // success and print call count
                caut_outs() << "non-assign: " << non_assign_stubs.size() << '\n';
                caut_outs() << "var-assign: " << var_assign_stubs.size() << '\n';

                caut_outs() << "non-assign list: " << str_join(",", non_assign_stubs) << '\n';
                caut_outs() << "var-assign list: "
                            << str_join<std::vector<std::pair<std::string, std::string>>::const_iterator>(
                                    ",",
                                    var_assign_stubs.begin(),
                                    var_assign_stubs.end(),
                                    [](std::vector<std::pair<std::string, std::string>>::const_iterator it) {
                                        return it->first + ":" + it->second;
                                    }) << '\n';
                if (LiftStubAssignVar.getValue()) {
                    SUCCESS_REWRITE:
                    if (LiftStubAssignVar.getValue()) {
                        if (MainDecl == nullptr) {
                            caut_errs() << "no main function found\n";
                            return;
                        }
                        std::string stub_decl_to_insert_at_begin_of_main;
                        for (const auto &pair : var_assign_stubs) {
                            stub_decl_to_insert_at_begin_of_main += (
                                    pair.first + " = __VERIFIER_nondet_" + pair.second + "();\n");
                        }
                        R.InsertTextAfterToken(MainDecl->getBody()->getBeginLoc(),
                                               stub_decl_to_insert_at_begin_of_main);
                    }
                    R.overwriteChangedFiles();
                }
                caut_success();
            } else {
                bool
                        ne = NonStubUpdateList.size() == non_assign_stubs.size(),
                        n0 = NonStubUpdateList.empty(),
                        ve = VarStubUpdateList.size() == var_assign_stubs.size(),
                        v0 = VarStubUpdateList.empty();
                // only success when do not have `neq` and have at least one type `eq` in number
                if ((ne || n0) && (ve || v0) && (ne || ve)) { goto SUCCESS_REWRITE; }
                else {
                    for (const auto &i : var_assign_stubs) {
                        caut_outs() << i.first << " " << i.second << "\n";
                    }
                    goto COUNTING_ERROR;
                }
            }
        } else {
            COUNTING_ERROR:
            caut_errs() << "counting error.\n";
        }
        caut_flush();
    }

    // count given function call
    bool TraverseCallExpr(clang::CallExpr *Call, DataRecursionQueue *Queue = nullptr) {
        StringRef stub_type;
        if (is_nondet_value(Call, &stub_type)) {
            bool return_value;
            if (handle_rewrite_nondet(Call, non_assign_stubs, NonStubUpdateList, return_value)) return return_value;

            non_assign_stubs.push_back(stub_type.str());
            return true;
        }
        return RecursiveASTVisitor::TraverseCallExpr(Call, Queue);
    }

    // handle all decl
    bool TraverseVarDecl(VarDecl *V) {
        if (V->hasInit()) {
            bool return_value;
            if (handle_assign_nondet(V->getInit(), V->getIdentifier()->getName().str(), return_value))
                return return_value;
        }
        return RecursiveASTVisitor::TraverseVarDecl(V);
    }

    // handle all assign stmt
    bool TraverseStmt(Stmt *S, DataRecursionQueue *Queue = nullptr) {
        if (S == nullptr) return true;
        if (auto Bin = dyn_cast<BinaryOperator>(S))
            if (Bin->isAssignmentOp())
                if (auto Left = dyn_cast<DeclRefExpr>(Bin->getLHS())) {
                    bool return_value;
                    if (handle_assign_nondet(Bin->getRHS(), Left->getNameInfo().getAsString(), return_value))
                        return return_value;
                }
        return RecursiveASTVisitor::TraverseStmt(S, Queue);
    }

    bool TraverseFunctionDecl(FunctionDecl *D) {
        if (LiftStubAssignVar.getValue() && D->getName().equals("main"))
            MainDecl = D;
        return RecursiveASTVisitor::TraverseFunctionDecl(D);
    }
};

int main(int argc, const char **argv) {
    NonStubUpdateList.addCategory(StubCountCategory);
    VarStubUpdateList.addCategory(StubCountCategory);
    LiftStubAssignVar.addCategory(StubCountCategory);
    LiftStubAssignVarPrefix.addCategory(StubCountCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, StubCountCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<StubCountTransformer>>().get());
}
