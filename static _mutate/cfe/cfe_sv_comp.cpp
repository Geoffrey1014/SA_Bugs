#include <random>
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"

#include "cfe_branch_visitor.hpp"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::OptionCategory SvCompCategory("Sv-comp transformer");

static llvm::cl::opt<bool> DeleteStubDecl("delete-stub-decl",
                                          llvm::cl::desc("if to delete sv-comp decl (extern, etc.)"),
                                          llvm::cl::init(true));

static llvm::cl::opt<bool> TransAssert("trans-assert",
                                       llvm::cl::desc("if to translate sv-comp `__VERIFIER_assert()` to `_err()`"),
                                       llvm::cl::init(true));

static llvm::cl::opt<bool> TransError("trans-error",
                                      llvm::cl::desc("if to translate sv-comp `__VERIFIER_error()` to `_err()`"),
                                      llvm::cl::init(true));

static llvm::cl::opt<bool> DelAssume("del-assume",
                                     llvm::cl::desc("if to delete `__VERIFIER_assume()`"),
                                     llvm::cl::init(true));

static llvm::cl::opt<bool> DelAtomic("del-atomic",
                                     llvm::cl::desc("if to delete `__VERIFIER_atomic_{begin,end}()`"),
                                     llvm::cl::init(true));

static llvm::cl::opt<bool> RanReplace("random-replace",
                                      llvm::cl::desc("if to randomly replace `__VERIFIER_nondet_*()` with value."),
                                      llvm::cl::init(true));

class SvCompRandGenerator {
private:
    std::random_device rd;
    std::mt19937 mt;
public:
    SvCompRandGenerator() : rd(), mt(rd()) {}

    template<typename T>
    T rand_i(T start, T end) {
        std::uniform_int_distribution<T> dist(start, end);
        return dist(mt);
    }

    template<typename T>
    T rand_f(T start, T end) {
        std::uniform_real_distribution<T> dist(start, next_float(end));
        return dist(mt);
    }
};

class SvCompTransformer : public clang::ASTConsumer,
                          public clang::RecursiveASTVisitor<SvCompTransformer> {
    CfeRewriter R;
    SvCompRandGenerator G;
public:
    void HandleTranslationUnit(ASTContext &Ctx) override {
        R.setSourceMgr(Ctx.getSourceManager(), Ctx.getLangOpts());

        if (RecursiveASTVisitor::TraverseDecl(Ctx.getTranslationUnitDecl())) {
            R.overwriteChangedFiles();
            caut_success();
        }
    }

    // delete all __VERIFIER_ decl
    bool TraverseFunctionDecl(FunctionDecl *D) {
        if (DeleteStubDecl.getValue() && D->getName().startswith("__VERIFIER_")) {
            SourceLocation decl_stmt_end_loc;
            if (!declSemiOrRBrac(D, R, decl_stmt_end_loc)) return false;

            return !(R.InsertTextBefore(D->getBeginLoc(), "/* ") ||
                     R.InsertTextAfterToken(decl_stmt_end_loc, " */"));
        } else {
            return RecursiveASTVisitor::TraverseFunctionDecl(D);
        }
    }

    bool TraverseCallExpr(CallExpr *Call, DataRecursionQueue *Queue = nullptr);
};

bool SvCompTransformer::TraverseCallExpr(clang::CallExpr *Call, DataRecursionQueue *Queue) {
    clang::StringRef callee_name;
    if (is_verifier_stub_call(Call, &callee_name)) {
        clang::StringRef nondet_type;
        if (RanReplace.getValue() && is_nondet_value(callee_name, &nondet_type)) {
            std::string r;

#define if_case(type, generator) if (nondet_type.equals(type)) r = to_str(generator())
            if_case("pointer", []() { return 0; });
            else if_case("pchar", []() { return 0; });

            else if_case("bool", [this]() { return G.rand_i(0, 1); });
            else if_case("int", [this]() { return G.rand_i(-5, 5); });
            else if_case("loff_t", [this]() { return G.rand_i(-5, 5); });
            else if_case("char", [this]() { return G.rand_i(-5, 5); });
            else if_case("long", [this]() { return G.rand_i(-5, 5); });
            else if_case("short", [this]() { return G.rand_i(-5, 5); });

            else if_case("unsigned", [this]() { return G.rand_i(0, 10); });
            else if_case("size_t", [this]() { return G.rand_i(0, 10); });
            else if_case("uint", [this]() { return G.rand_i(0, 10); });
            else if_case("u32", [this]() { return G.rand_i(0, 10); });
            else if_case("uchar", [this]() { return G.rand_i(0, 10); });
            else if_case("ulong", [this]() { return G.rand_i(0, 10); });
            else if_case("ushort", [this]() { return G.rand_i(0, 10); });

            else if_case("double", [this]() { return G.rand_f(-5.0, 5.0); });
            else if_case("float", [this]() { return G.rand_f(-5.0f, 5.0f); }) + "f";
#undef case_type
            else {
                caut_errs() << "unsupported nondet value: " << nondet_type << "\n";
                return false;
            }

            return !(R.InsertTextBefore(Call->getBeginLoc(), "/* ") ||
                     R.InsertTextAfterToken(Call->getEndLoc(), " */ " + r));
        } else if (TransAssert.getValue() && callee_name.equals("__VERIFIER_assert")) {
            // __VERIFIER_assert(b); => if (! (b) ) { _err(); } else {};
            R.ReplaceText(Call->getBeginLoc(), 17, "if (! ");
            R.InsertTextAfterToken(Call->getRParenLoc(), " ) { _err(); } else {}");
        } else if (TransError.getValue() && callee_name.equals("__VERIFIER_error")) {
            R.ReplaceText(Call->getBeginLoc(), 16, "_err");
        } else if ((DelAssume.getValue() && callee_name.equals("__VERIFIER_assume")) ||
                   (DelAtomic.getValue() && callee_name.startswith("__VERIFIER_atomic_"))) {
            SourceLocation semi;
            if (!stmtSemi(Call, R, semi)) return false;

            return !(R.InsertTextBefore(Call->getBeginLoc(), "/* ") ||
                     R.InsertTextAfterToken(semi, " */"));
        }
    }
    return RecursiveASTVisitor::TraverseCallExpr(Call, Queue);
}

int main(int argc, const char **argv) {
    DeleteStubDecl.addCategory(SvCompCategory);
    TransAssert.addCategory(SvCompCategory);
    TransError.addCategory(SvCompCategory);
    DelAssume.addCategory(SvCompCategory);
    DelAtomic.addCategory(SvCompCategory);
    RanReplace.addCategory(SvCompCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, SvCompCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<SvCompTransformer>>().get());
}
