#include <cassert>
#include <sstream>
#include <deque>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"

#include "cfe_utils.hpp"
#include "llvm/Support/raw_ostream.h"

using namespace clang;
using namespace llvm;
using namespace clang::tooling;


static llvm::cl::OptionCategory PreprocessToolCategory("Preprocess unit for cfe tool");

static llvm::cl::opt<bool> MkCompound("mk-compound",
                                      llvm::cl::desc("wrap if stmt with compound"),
                                      llvm::cl::init(true));

static llvm::cl::opt<bool> MkElse("mk-else",
                                  llvm::cl::desc("generate empty else stmt"),
                                  llvm::cl::init(true));
typedef std::deque<std::string> CompoundQueue;

class PreprocessTransformer : public clang::ASTConsumer,
                              public clang::RecursiveASTVisitor<PreprocessTransformer> {
private :
    CfeRewriter R;
    clang::FunctionDecl *MainDecl = nullptr;

    int random_var_count = 0;

    std::string get_random_var_name(bool next = false) {
        return std::string() + "__caut_tmp_" + to_str(next ? ++random_var_count : random_var_count);
    }

public:
    void HandleTranslationUnit(ASTContext &Ctx) override;

    bool TraverseVarDecl(VarDecl *V);

    bool TraverseFunctionDecl(FunctionDecl *F);

    bool TraverseStmt(Stmt *S, DataRecursionQueue *Queue = nullptr, CompoundQueue *compoundQueue = nullptr);
};

void PreprocessTransformer::HandleTranslationUnit(ASTContext &Ctx) {
    R.setSourceMgr(Ctx.getSourceManager(), Ctx.getLangOpts());
    // R.InsertTextBefore(Ctx.getTranslationUnitDecl()->getBeginLoc() , "#include HWG");
    // llvm::errs() << "\n getMainFileID isValid : " << Ctx.getSourceManager().getMainFileID().isValid() << "\n";

    if (TraverseDecl(Ctx.getTranslationUnitDecl())) {
        if (MainDecl == nullptr) {
            caut_errs() << "no main func\n";
        } else {
            if (auto C = cast<CompoundStmt>(MainDecl->getBody())) {
                if (C->body_empty()
                    || (*(C->body_rbegin()))->getStmtClass() != Stmt::ReturnStmtClass)
                    R.InsertTextBefore(MainDecl->getBodyRBrace(), "return 0; ");
            }
            R.overwriteChangedFiles();
            caut_success();
        }
    }
}

bool PreprocessTransformer::TraverseFunctionDecl(FunctionDecl *F) {
    llvm::errs() << "TraverseFunctionDecl: " << F->getName() << "\n";
    if (F->getIdentifier() != nullptr && (F->getName().equals("main"))) {
        MainDecl = F;
    }
    return RecursiveASTVisitor::TraverseFunctionDecl(F);
}

bool PreprocessTransformer::TraverseVarDecl(VarDecl *V) {
    llvm::errs() << "TraverseVarDecl " << V->getName() <<  "\n" << "Type: " << V->getType() << "\n";

    if (!V->hasInit()) {
        if (auto ArrayTypeOfDecl = dyn_cast<ArrayType>(V->getType())) {
            SourceLocation semi;
            if (declSemi(V, R, semi) && ArrayTypeOfDecl->getElementType()->isBuiltinType()) {
                if (V->getType()->getTypeClass() == clang::Type::TypeClass::ConstantArray) {
                    // for const-length array, use = {0} to initialize
                    // https://en.cppreference.com/w/c/language/array_initialization
                    R.InsertTextBefore(semi, "/**/ = {0}/**/");
                    return true;
                } else if (auto VariableArrayTypeInstance = dyn_cast<VariableArrayType>(V->getType())) {
                    // for var-length array, use for-loop
                    std::string array_size, array_name;

                    array_name = V->getIdentifier()->getName().str();

                    // only do this when size expression is one single var
                    // don't know why there's an ImplicitCast here
                    Expr *array_size_var = VariableArrayTypeInstance->getSizeExpr();
                    while (auto cast_array_size_var = dyn_cast<CastExpr>(array_size_var))
                        array_size_var = cast_array_size_var->getSubExpr();

                    if (auto size_var_ref = dyn_cast<DeclRefExpr>(array_size_var)) {
                        array_size = size_var_ref->getNameInfo().getAsString();

                        std::ostringstream out_str;
                        // for (int x = 0; x < N; ++x) { arr[x] = 0; }
                        out_str << "for (int " << get_random_var_name(true) << " = 0;"
                                << get_random_var_name() << " < " << array_size << ";"
                                << "++" << get_random_var_name() << ")"
                                << "{ " << array_name << "[" << get_random_var_name() << "] = 0; }";

                        R.InsertTextAfterToken(semi, out_str.str());
                        return true;
                    }
                }
            }
        }
    }

    return RecursiveASTVisitor::TraverseVarDecl(V);
}

bool
PreprocessTransformer::TraverseStmt(Stmt *S, RecursiveASTVisitor<PreprocessTransformer>::DataRecursionQueue *Queue,
                                    CompoundQueue *compoundQueue) {
    if (S == nullptr) {
        return true;
    } else if (S->getBeginLoc().isMacroID() and S->getEndLoc().isMacroID()) {
        return true;
    }

    if (compoundQueue == nullptr)
        compoundQueue = new CompoundQueue();

    Stmt::StmtClass sc = S->getStmtClass();

    bool mkCompound = MkCompound.getValue(), process_post_queue = compoundQueue->empty();

    auto handle_stmt_push_back_brace = [mkCompound, this](Stmt *S, CompoundQueue *compoundQueue) {
        if (mkCompound && !isa<CompoundStmt>(S)) {
            this->R.InsertTextBefore(S->getBeginLoc(), "{ ");
            compoundQueue->push_back(" }");
        }
    };

    auto insert_clear_queue = [mkCompound, this](SourceLocation post_loc, CompoundQueue *compoundQueue) {
        std::string post_text;
        while (mkCompound && !compoundQueue->empty()) {
            post_text += compoundQueue->back();
            compoundQueue->pop_back();
        }
        if (!post_text.empty())
            R.InsertTextAfterToken(post_loc, post_text);
    };

    auto insert_current = [handle_stmt_push_back_brace, insert_clear_queue, this, Queue](Stmt *S) {
        auto currentQueue = new CompoundQueue();
        handle_stmt_push_back_brace(S, currentQueue);

        this->TraverseStmt(S, Queue, currentQueue);

        SourceLocation cur_end_loc;
        if (stmtSemiOrRBrac(S, R, cur_end_loc))
            insert_clear_queue(cur_end_loc, currentQueue);
        else {
            caut_errs() << "semi not found on then branch of if stmt\n";
            return false;
        }
        return true;
    };

    auto handle_stmt_finalize_queue = [process_post_queue, insert_clear_queue, this, Queue, compoundQueue](Stmt *S) {
        bool _r = this->TraverseStmt(S, Queue, compoundQueue);
        if (process_post_queue && !compoundQueue->empty()) {
            SourceLocation end;
            if (auto CompoundThen = dyn_cast<CompoundStmt>(S)) {
                end = CompoundThen->getRBracLoc();
            } else if (!stmtSemiOrRBrac(S, R, end)) {
                caut_errs() << "no semi found at loc.\n";
                return false;
            }
            insert_clear_queue(end, compoundQueue);
        }
        return _r;
    };

    switch (sc) {
        case Stmt::IfStmtClass: {
            auto *If = cast<IfStmt>(S);

            Stmt *FinStmt;

            if (If->getElse() == nullptr) {
                if (MkElse.getValue())
                    compoundQueue->push_back(" else {}");

                FinStmt = If->getThen();
            } else {
                if (!insert_current(If->getThen())) return false;

                FinStmt = If->getElse();
            }

            handle_stmt_push_back_brace(FinStmt, compoundQueue);
            return handle_stmt_finalize_queue(FinStmt);
        }
        case Stmt::DoStmtClass: {
            auto DoWhile = cast<DoStmt>(S);

            if (!insert_current(DoWhile->getBody())) return false;

            return TraverseStmt(DoWhile->getCond(), Queue);
        }
        case Stmt::WhileStmtClass:
        case Stmt::ForStmtClass: {
            Stmt *Body = nullptr;
            if (auto For = dyn_cast<ForStmt>(S)) {
                Body = For->getBody();
            } else if (auto While = dyn_cast<WhileStmt>(S)) {
                Body = While->getBody();
            }
            assert(Body != nullptr);

            handle_stmt_push_back_brace(Body, compoundQueue);

            return handle_stmt_finalize_queue(Body);
        }
        case Stmt::SwitchStmtClass: {
            auto Switch = cast<SwitchStmt>(S);
            auto case_i = Switch->getSwitchCaseList();
            while (case_i != nullptr) {
                if (!insert_current(case_i->getSubStmt()))
                    return false;
                case_i = case_i->getNextSwitchCase();
            }
            return true;
        }
        default: {
            return RecursiveASTVisitor::TraverseStmt(S, Queue);
        }
    }
}

int main(int argc, const char **argv) {
    MkCompound.addCategory(PreprocessToolCategory);
    MkElse.addCategory(PreprocessToolCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, PreprocessToolCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<PreprocessTransformer>>().get());
}
