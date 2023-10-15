#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "cfe_utils.hpp"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::opt<std::string> StubFunctionToReduce("stub-function-to-reduce",
                                                       llvm::cl::init("_stub"));

static llvm::cl::opt<int> BranchToReduce(
        "branch-to-reduce", llvm::cl::init(0),
        llvm::cl::desc("condition to delete, starting from 1, 0 means to just print total number."));


static llvm::cl::OptionCategory StubReduceCategory("Stub Condition Reducer");

class StubReduceTransformer : public clang::ASTConsumer,
                              public clang::RecursiveASTVisitor<StubReduceTransformer> {
    using tree_type = std::vector<std::pair<int, int>>;

    CfeRewriter R;
    bool at_func = false;

    int cond_count = 0;

    std::vector<int> tree;

    enum condition_direction {
        SHRINK = false,
        ENLARGE = true,
    };

    condition_direction flip(condition_direction c) {
        return c == SHRINK ? ENLARGE : SHRINK;
    }

public:
    void HandleTranslationUnit(ASTContext &Ctx) override {
        R.setSourceMgr(Ctx.getSourceManager(), Ctx.getLangOpts());

        if (RecursiveASTVisitor::TraverseDecl(Ctx.getTranslationUnitDecl())) {
            if (BranchToReduce.getValue() <= cond_count) {
                if (BranchToReduce.getValue() == 0) {
                    caut_outs() << "deletable items: " << str_join<std::vector<int>::const_iterator>(
                            ";", tree.begin(), tree.end(),
                            [](std::vector<int>::const_iterator i) { return to_str(*i); })
                                << "\n";
                } else {
                    R.overwriteChangedFiles();
                }
                caut_success();
            } else {
                caut_errs() << "branch index overflow\n";
            }
        }
    }

    // neg indicates how the tendency of current subexpr will affect whole bool expr.
    // neg == false means if the range of current expr enlarges, the range of whole expr shrinkes.
    // so it's save to delete branch of LAnd iff neg == true or branch and LOr iff neg == false.
    int HandleIfCond(Expr *E, condition_direction direction_target = SHRINK) {
        std::string not_support_op_code;
        if (auto BinExpr = dyn_cast<BinaryOperator>(E)) {
            if (BinExpr->getOpcode() == BinaryOperatorKind::BO_LAnd ||
                BinExpr->getOpcode() == BinaryOperatorKind::BO_LOr) {

                ///         | target | delete | modify
                /// --------|--------|--------|--------
                ///  a && b | ↑      | √      | ↑
                ///         | ↓      | ×      | ↓
                ///  a || b | ↑      | ×      | ↑
                ///         | ↓      | √      | ↓
                bool can_delete = (BinExpr->getOpcode() == BinaryOperatorKind::BO_LOr) == (direction_target == SHRINK);

                int
                        current_count = ++cond_count,
                        left_count = HandleIfCond(BinExpr->getLHS(), direction_target),
                        right_count = HandleIfCond(BinExpr->getRHS(), direction_target);

                if (can_delete) {
                    if (BranchToReduce.getValue() == left_count) {
                        R.RemoveText(SourceRange(BinExpr->getLHS()->getBeginLoc(), BinExpr->getOperatorLoc()));
                    } else if (BranchToReduce.getValue() == right_count) {
                        R.RemoveText(SourceRange(BinExpr->getOperatorLoc(), BinExpr->getRHS()->getEndLoc()));
                    }
                    tree.emplace_back(left_count);
                    tree.emplace_back(right_count);
                }

                if (left_count == right_count) {
                    caut_errs() << BinExpr->getLHS()->getBeginLoc().printToString(R.getSourceMgr()) << "\n "
                                << BinExpr->getRHS()->getBeginLoc().printToString(R.getSourceMgr()) << "\n";
                    return -1;
                }

                return current_count;
            } else if (
                    BinExpr->getOpcode() == BinaryOperatorKind::BO_LT ||
                    BinExpr->getOpcode() == BinaryOperatorKind::BO_GT ||
                    BinExpr->getOpcode() == BinaryOperatorKind::BO_LE ||
                    BinExpr->getOpcode() == BinaryOperatorKind::BO_GE ||
                    BinExpr->getOpcode() == BinaryOperatorKind::BO_EQ) {
                goto LEAF;
            } else {
                not_support_op_code = BinExpr->getOpcodeStr().str();
            }
        } else if (IntegerLiteral::classof(E) || DeclRefExpr::classof(E)) {
            LEAF:
            return ++cond_count;
        } else if (auto NegExpr = dyn_cast<UnaryOperator>(E)) {
            if (NegExpr->getOpcode() == UnaryOperatorKind::UO_LNot) {
                return HandleIfCond(NegExpr->getSubExpr(), flip(direction_target));
            } else {
                not_support_op_code = BinExpr->getOpcodeStr().str();
            }
        } else if (auto Paren = dyn_cast<ParenExpr>(E)) {
            return HandleIfCond(Paren->getSubExpr(), direction_target);
        }
        // pretty print
        if (!not_support_op_code.empty()) not_support_op_code = " " + not_support_op_code;
        caut_errs() << "condition not supported: " << E->getStmtClassName() << not_support_op_code << "\n";
        return -1;
    }


    bool TraverseIfStmt(IfStmt *S, DataRecursionQueue *Queue = nullptr) {
        // simple replacement for if/then/else
        if (at_func) {
            return HandleIfCond(S->getCond()) > 0 &&
                   TraverseStmt(S->getThen()) &&
                   TraverseStmt(S->getElse());
        } else
            return RecursiveASTVisitor::TraverseIfStmt(S, Queue);
    }

    bool TraverseFunctionDecl(FunctionDecl *D) {
        std::string s = D->getName().str();
        bool _at_func = D->getName().equals(StubFunctionToReduce.getValue());
        if (_at_func) this->at_func = true;
        bool result = RecursiveASTVisitor::TraverseFunctionDecl(D);
        if (_at_func) this->at_func = false;
        return result;
    }
};

int main(int argc, const char **argv) {
    StubFunctionToReduce.addCategory(StubReduceCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, StubReduceCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<StubReduceTransformer>>().get());
}