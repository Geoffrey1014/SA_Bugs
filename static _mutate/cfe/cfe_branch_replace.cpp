#include "cfe_branch_visitor.hpp"
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"

static llvm::cl::OptionCategory BranchReplaceCategory("Branch replace transformer");


class BranchReplace : public BranchVisitor<BranchReplace, false> {
    void TraverseSuccess() override {
        if (TargetBranch.getValue() > branch_count)
            caut_errs() << "branch target invalid.\n";
        else if (TargetBranch.getValue() > 0) {
            R.overwriteChangedFiles();
        }
    }

    bool HandleWithBranch(BrCount br, Stmt *S) override {
        if (TargetBranch.getValue() == br) {
            if (auto Compound = dyn_cast<CompoundStmt>(S)) {
                R.InsertTextAfterToken(Compound->getLBracLoc(), STUB_FUNC_CALL_STMT(ErrStub));
            } else {
                SourceLocation loc_start = S->getBeginLoc(), loc_end;
                if (!stmtSemiOrRBrac(S, R, loc_end)) return false;
                R.ReplaceText(SourceRange(loc_start, loc_end), STUB_FUNC_CALL_STMT(ErrStub));
            }
        }
        return true;
    }

    bool HandleWithBranch(BrCount br, Expr *E) override {
        if (TargetBranch.getValue() == br) {
            R.InsertTextBefore(E->getBeginLoc(), "( " + STUB_FUNC_CALL(ErrStub) + ", ");
            R.InsertTextAfterToken(E->getEndLoc(), " )");
        }
        return true;
    }
};


int main(int argc, const char **argv) {
    ErrStub.addCategory(BranchReplaceCategory);
    with_desc(TargetBranch, "branch to replace, starts from 1").addCategory(BranchReplaceCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, BranchReplaceCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<BranchReplace>>().get());
}
