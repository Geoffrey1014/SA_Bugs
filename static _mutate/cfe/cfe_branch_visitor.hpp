#ifndef CFE_TOOLING_CFE_BRANCH_VISITOR_H
#define CFE_TOOLING_CFE_BRANCH_VISITOR_H
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"

#include "cfe_utils.hpp"

using namespace clang;
using namespace clang::tooling;

typedef unsigned long long BrCount;


const std::string DEFAULT_FLAG_PREFIX = "_br_";
const std::string DEFAULT_STUB_FUNC = "_stub";
const std::string DEFAULT_ERR_STUB_FUNC = "_err";
const std::string DEFAULT_WRAP_FUNC = "_wrap";

const std::vector<std::string> exit_points = std::vector<std::string>{"exit", "__builtin_exit"};
const std::vector<std::string> abort_points = std::vector<std::string>{"abort", "__builtin_abort"};
const std::vector<std::string> assert_points = std::vector<std::string>{"__assert_fail"};

static llvm::cl::opt<std::string> FlagPreFix("flag-pre",
                                             llvm::cl::desc("prefix for flag vars"),
                                             llvm::cl::init(DEFAULT_FLAG_PREFIX));

static llvm::cl::opt<std::string> Stub("stub",
                                       llvm::cl::desc("finalize stub for main, check brs"),
                                       llvm::cl::init(DEFAULT_STUB_FUNC));

static llvm::cl::opt<std::string> ErrStub("err-stub",
                                          llvm::cl::desc("finalize stub for main"),
                                          llvm::cl::init(DEFAULT_ERR_STUB_FUNC));

static llvm::cl::opt<std::string> FuncWrap("func-wrap",
                                           llvm::cl::desc("wrapper for function call"),
                                           llvm::cl::init(DEFAULT_WRAP_FUNC));

static llvm::cl::opt<BrCount> TargetBranch("branch-target",
                                           llvm::cl::desc("target branch of transformation, starts from 1"),
                                           llvm::cl::init(0));

/*
 * replace help string of opt used in other tool
 */
template<typename T>
llvm::cl::opt<T> &with_desc(llvm::cl::opt<T> &_opt, llvm::StringRef desc) {
    _opt.setDescription(desc);
    return _opt;
}

template<typename T>
llvm::cl::opt<T> &with_arg_str(llvm::cl::opt<T> &_opt, llvm::StringRef arg_str) {
    _opt.setArgStr(arg_str);
    return _opt;
}


#define STUB_FUNC_CALL(opt) ((opt).getValue() + "()")
#define STUB_FUNC_CALL_STMT(opt) STUB_FUNC_CALL(opt) + ";"


template<typename Derived, bool check_main = false>
class BranchVisitor : public clang::ASTConsumer, public clang::RecursiveASTVisitor<Derived> {
protected:
    CfeRewriter R;
    BrCount branch_count = 0;
    bool at_main = false;
    clang::FunctionDecl *MainDecl = nullptr;

public:
    bool print_branch_count = true;

    void HandleTranslationUnit(ASTContext &Ctx) override;

    bool TraverseFunctionDecl(FunctionDecl *F) {
        if (check_main) {
            bool is_main = false;
            if (F->getIdentifier() != nullptr && (is_main = F->getName().equals("main"))) {
                MainDecl = F;
            }
            if (is_main)
                at_main = true;
            bool res = RecursiveASTVisitor<Derived>::TraverseFunctionDecl(F);
            if (is_main)
                at_main = false;
            return res;
        } else
            return RecursiveASTVisitor<Derived>::TraverseFunctionDecl(F);
    }

    bool TraverseStmt(Stmt *S, typename RecursiveASTVisitor<Derived>::DataRecursionQueue *Queue = nullptr);

    virtual bool HandleWithBranch(BrCount br, Stmt *S) = 0;

    virtual bool HandleWithBranch(BrCount br, Expr *E) = 0;

    virtual void TraverseSuccess() { R.overwriteChangedFiles(); };
};

template<typename Derived, bool check_main>
void BranchVisitor<Derived, check_main>::HandleTranslationUnit(ASTContext &Ctx) {
    R.setSourceMgr(Ctx.getSourceManager(), Ctx.getLangOpts());

    if (RecursiveASTVisitor<Derived>::TraverseDecl(Ctx.getTranslationUnitDecl())) {
        if (check_main && MainDecl == nullptr)
            caut_errs() << "no main function.\n";
        else {
            if (this->print_branch_count) {
                caut_outs() << "branch count " << this->branch_count << "\n";
            }
            TraverseSuccess();
        }
    }
}


template<typename Derived, bool check_main>
bool
BranchVisitor<Derived, check_main>::TraverseStmt(Stmt *S,
                                                 typename RecursiveASTVisitor<Derived>::DataRecursionQueue *Queue) {
    if (S == nullptr) return true;

    switch (S->getStmtClass()) {
        case Stmt::IfStmtClass: {
            auto If = cast<IfStmt>(S);
            if (!If->getBeginLoc().isMacroID() && If->getElse() == nullptr) {
                caut_errs() << "empty else\n";
                return false;
            }
            if (!HandleWithBranch(branch_count += 1, If->getThen())) return false;
            if (!HandleWithBranch(branch_count += 1, If->getElse())) return false;
            return RecursiveASTVisitor<Derived>::TraverseIfStmt(If, Queue);
        }
        case Stmt::ConditionalOperatorClass: {
            auto Cond = cast<ConditionalOperator>(S);
            if (!HandleWithBranch(branch_count += 1, Cond->getTrueExpr())) return false;
            if (!HandleWithBranch(branch_count += 1, Cond->getFalseExpr())) return false;
            return RecursiveASTVisitor<Derived>::TraverseConditionalOperator(Cond, Queue);
        }
        case Stmt::WhileStmtClass:
        case Stmt::ForStmtClass:
        case Stmt::DoStmtClass: {
            Stmt *Body = nullptr;
            if (auto While = dyn_cast<WhileStmt>(S))
                Body = While->getBody();
            else if (auto For = dyn_cast<ForStmt>(S))
                Body = For->getBody();
            else if (auto DoWhile = dyn_cast<DoStmt>(S))
                Body = DoWhile->getBody();
            else
                assert(Body != nullptr);

            if (!HandleWithBranch(branch_count += 1, Body)) return false;
            return RecursiveASTVisitor<Derived>::TraverseStmt(S, Queue);
        }
        case Stmt::SwitchStmtClass: {
            auto Switch = cast<SwitchStmt>(S);
            auto case_i = Switch->getSwitchCaseList();
            while (case_i != nullptr) {
                if (!HandleWithBranch(branch_count += 1, case_i->getSubStmt())) return false;
                case_i = case_i->getNextSwitchCase();
            }
            return RecursiveASTVisitor<Derived>::TraverseSwitchStmt(Switch, Queue);
        }
        default: {
            return RecursiveASTVisitor<Derived>::TraverseStmt(S, Queue);
        }
    }
}

#endif //CFE_TOOLING_CFE_BRANCH_VISITOR_H