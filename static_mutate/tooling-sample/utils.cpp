
#include <string>
#include <vector>
#include "llvm/Support/raw_ostream.h"
#include "clang/AST/Type.h"
using namespace clang;

template<typename T>
void bo_and_rules(std::string exprStr, std::string LExprStr, std::string RExprStr,std::vector<T> & exprEvelVector){
        llvm::errs() << "\n  bo_and_rules: " << exprStr <<" \n";
              // exprEvelVector.push_back(std::string() + "(" + "bo_and_rules" + ")" + "==" + "true");

      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true");
      exprEvelVector.push_back(std::string() + "(" + "!" + "(" + exprStr + ")" + ")" + "==" + "false");
      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "||" + "(" + "!"  + "(" + RExprStr + ")" + + ")" ")" + "==" + "false");

      exprEvelVector.push_back(LExprStr); // a
      exprEvelVector.push_back(RExprStr); // b
      exprEvelVector.push_back(std::string() + "(" + "!" + "(" + LExprStr + ")" + ")" + "==" + "false"); // !a == false
      exprEvelVector.push_back(std::string() + "(" + "!" + "(" + RExprStr + ")" + ")" + "==" + "false"); // !b == false

      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "&&" +  "(" + RExprStr + ")" + ")" + "==" + "true");  // a && b == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "&&" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // b && a == true

      exprEvelVector.push_back(std::string() + "!" + "(" + "(" + LExprStr + ")" + "&&" +  "(" + RExprStr + ")" + ")" + "==" + "false"); // !(a && b) == false
      exprEvelVector.push_back(std::string() + "!" + "(" + "(" + RExprStr + ")" + "&&" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // !(b && a) == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "&&" + "(" + "!"  + "(" + RExprStr + ")" + ")" ")" + "==" + "false");  // !a && !b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "&&" + "(" + "!"  + "(" + LExprStr + ")" + ")" ")" + "==" + "false"); //  !b && !a == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "||" + "(" + "!"  + "(" + RExprStr + ")" + ")" ")" + "==" + "false"); // !a || !b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "||" + "(" + "!"  + "(" + LExprStr + ")" + ")" ")" + "==" + "false"); // // !b && !a == false


      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "&&" +  "(" + RExprStr + ")" + ")" + "==" + "false"); // !a && b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "&&" + "(" + "!"  + "(" + LExprStr + ")" + + ")" ")" + "==" + "false"); // b && !a == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "&&" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // !b && a == false
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "&&" + "(" + "!"  + "(" + RExprStr + ")" + + ")" ")" + "==" + "false"); // a && !b == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "||" +  "(" + RExprStr + ")" + ")" + "==" + "true"); // !a || b == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "||" + "(" + "!"  + "(" + LExprStr + ")" + + ")" ")" + "==" + "true"); // b || !a == true

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "||" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // !b || a == true
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "||" + "(" + "!"  + "(" + RExprStr + ")" + + ")" ")" + "==" + "true"); // a || !b == true

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "&&" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // !a && a == false
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "&&" + "(" + "!"  + "(" + LExprStr + ")" + + ")" ")" + "==" + "false"); // a && !a == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "&&" +  "(" +RExprStr + ")" + ")" + "==" + "false"); // !b && b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "&&" + "(" + "!"  + "(" + RExprStr + ")" + + ")" ")" + "==" + "false"); // b && !b == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "||" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // !a || a == true
      exprEvelVector.push_back(std::string() + "(" + "(" +LExprStr + ")" + "||" + "(" + "!"  + "(" + LExprStr + ")" + + ")" ")" + "==" + "true"); // a || !a == true

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + RExprStr + ")" + ")" + "||" +  "(" + RExprStr + ")" + ")" + "==" + "true"); // !b || a == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "||" + "(" + "!"  + "(" + RExprStr + ")" + + ")" ")" + "==" + "true"); // a || !b == true

      exprEvelVector.push_back("true");
}



template<typename T>
void bo_or_rules(std::string exprStr, std::string LExprStr, std::string RExprStr,std::vector<T> & exprEvelVector){
    // llvm::errs() << "\n  BO_LOr: " <<  opcode << " \n";
          // exprEvelVector.push_back(std::string() + "(" + "bo_or_rules" + ")" + "==" + "true");

      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true");
      exprEvelVector.push_back(std::string() + "(" + "!" + "(" + exprStr + ")" + ")" + "==" + "false");

      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "||" +  "(" + RExprStr + ")" + ")" + "==" + "true");  // a || b == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "||" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // b || a == true

      exprEvelVector.push_back(std::string() + "!" + "(" + "(" + LExprStr + ")" + "||" +  "(" + RExprStr + ")" + ")" + "==" + "false"); // !(a || b) == false
      exprEvelVector.push_back(std::string() + "!" + "(" + "(" + RExprStr + ")" + "||" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // !(b || a) == false

      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" + LExprStr + ")" + ")" + "&&" +  "(" + "!"  + "(" + RExprStr + ")" + ")" + ")" + "==" + "false"); // !a && !b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + "!" + "(" +RExprStr + ")" + ")" + "&&" +  "(" + "!"  + "(" + LExprStr + ")" + ")" + ")" + "==" + "false"); // !b && !a == false

      exprEvelVector.push_back("true");

}

template<typename T>
void handle_left_type(std::vector<T> & exprEvelVector, std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector, std::string LExprStr, QualType typeL, std::string RExprStr){
  if (const auto *BTL = dyn_cast<BuiltinType>(typeL.getCanonicalType())){
    llvm::errs() << "\n Left Side Kind: " <<  BTL->getKind() << " \n";
    switch (BTL->getKind()) {
      case BuiltinType::Char_U:
      case BuiltinType::UChar:
      case BuiltinType::UShort:
      case BuiltinType::UInt:
      case BuiltinType::ULong:
      case BuiltinType::ULongLong:
        exprEvelVector2.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")"); // a - 1 < b
        ifCondVector.push_back( std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= 0");
        break;
      case BuiltinType::Char_S:
      case BuiltinType::SChar:
        exprEvelVector2.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" ); // a - 1 < b
        ifCondVector.push_back(std::string() +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT8_MIN");
        break;
      case BuiltinType::Short:
        exprEvelVector2.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" ); // a - 1 < b
        ifCondVector.push_back(std::string() +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT16_MIN");
        break;
      case BuiltinType::Int:
        exprEvelVector2.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" ); // a - 1 < b
        ifCondVector.push_back(std::string() +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT32_MIN" );
        break;
      case BuiltinType::Long:
      case BuiltinType::LongLong:
        exprEvelVector2.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" ); // a - 1 < b
        ifCondVector.push_back(std::string() +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT64_MIN");
        break;
      default:
      break;
    }
  }
}

template<typename T>
void bo_eq_rules(std::string exprStr, std::string LExprStr, QualType typeL, std::string RExprStr,QualType typeR, std::vector<T> & exprEvelVector , std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector){
    // Fact
      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true"); // a == b == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "==" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // b == a == true

      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "!=" +  "(" + RExprStr + ")" + ")" + "==" + "false"); // a != b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "!=" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // b != a == false

              
        if (const auto *BTR = dyn_cast<BuiltinType>(typeR.getCanonicalType())){
            llvm::errs() << "\n  Kind: " <<  BTR->getKind() << " \n";
            // Add a positive number
            exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "==" + "(" + "(" + RExprStr + ")" + "+" + "0" + ")");

            switch (BTR->getKind()) {
              case BuiltinType::Bool:  
                exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  + " && " + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX"); // a < b +1
                exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" + " && " +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT32_MIN"); // a - 1 < b
                break;

              case BuiltinType::Char_U:
              case BuiltinType::UChar:
                exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a < b +1
                ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT8_MAX");
                handle_left_type(exprEvelVector, exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
                break;

              case BuiltinType::UShort:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
            case BuiltinType::UInt:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
          
            case BuiltinType::ULong:
            case BuiltinType::ULongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" );
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            
            case BuiltinType::Char_S:
            case BuiltinType::SChar:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT8_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            case BuiltinType::Short:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            case BuiltinType::Int:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
            
            case BuiltinType::Long:
            case BuiltinType::LongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  ); // a < b + 1
              ifCondVector.push_back( std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
          
              default:
                break;
            }
        }
        else if (const auto *BTR = dyn_cast<ArrayType>(typeR.getCanonicalType()) ){
          exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
        }
        else if  ( const auto *BTR = dyn_cast<PointerType>(typeR.getCanonicalType()) ){
        exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
          exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "==" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "2" + ")" + "==" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
        }

        exprEvelVector.push_back("true");

}


template<typename T>
void bo_lt_rules(std::string exprStr, std::string LExprStr, QualType typeL, std::string RExprStr,QualType typeR, std::vector<T> & exprEvelVector , std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector){
  //  llvm::errs() << "\n  BO_LT: " <<  opcode << " \n";

      // Fact
      // exprEvelVector.push_back(std::string() + "(bo_lt_rules)" + "==" + "true"); // a < b == true
      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true"); // a < b == true
      exprEvelVector.push_back(std::string() + "(" + RExprStr + ")" + ">" + "(" + LExprStr + ")" + "==" + "true"); // b > a == true


      // Add an equal
      exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + RExprStr + ")" + "==" + "true"); // a <= b == true
      exprEvelVector.push_back(std::string() + "(" + RExprStr + ")" + ">=" + "(" + LExprStr + ")" + "==" + "true"); // b >= a == true

        
      if (const auto *BTR = dyn_cast<BuiltinType>(typeR.getCanonicalType())){
          llvm::errs() << "\n Right Side Kind: " <<  BTR->getKind() << " \n";
          // Add a positive number
          exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "0" + ")"); //a + 0 < b + 0

          switch (BTR->getKind()) {
            case BuiltinType::Bool:  // TODO: 在标准中没看到 bool 的数值运算的规定
              exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  + " && " + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX"); // a < b + 1
              exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<" +  "(" + RExprStr + ")" + " && " +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT32_MIN"); // a - 1 < b
              break;

            case BuiltinType::Char_U:
            case BuiltinType::UChar:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT8_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            case BuiltinType::UShort:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
            case BuiltinType::UInt:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
          
            case BuiltinType::ULong:
            case BuiltinType::ULongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" );
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            
            case BuiltinType::Char_S:
            case BuiltinType::SChar:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT8_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            case BuiltinType::Short:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;

            case BuiltinType::Int:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a < b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
            
            case BuiltinType::Long:
            case BuiltinType::LongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  ); // a < b + 1
              ifCondVector.push_back( std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 < b
              break;
        
            default:
              break;
          }
      }
      else if (const auto *BTL = dyn_cast<ArrayType>(typeR.getCanonicalType()) ){
        // exprEvelVector.push_back(std::string() + "ARRAY TYPE");
        // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
        exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "-" + "1" + ")" ); // a <= b -1

      }
      else if  ( const auto *BTL = dyn_cast<PointerType>(typeR.getCanonicalType()) ){
        // exprEvelVector.push_back(std::string() + "POINTER TYPE");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "<=" + "(" + RExprStr + ")");
      // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "2" + ")" + "==" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      }
      else{
        llvm::errs() << "\n Other Kind: " <<  typeR.getCanonicalType() << " \n";
      }

      exprEvelVector.push_back("true");
      // return false;

}


template<typename T>
void bo_gt_rules(std::string exprStr, std::string LExprStr, QualType typeL, std::string RExprStr,QualType typeR, std::vector<T> & exprEvelVector , std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector){
       // llvm::errs() << "\n  BO_GT: " <<  opcode << " \n";

      // "a > b"   is equal to " b <  a "
      bo_lt_rules(exprStr, RExprStr, typeR, LExprStr, typeL, exprEvelVector, exprEvelVector2, ifCondVector);

}

template<typename T>
void bo_le_rules(std::string exprStr, std::string LExprStr, QualType typeL, std::string RExprStr,QualType typeR, std::vector<T> & exprEvelVector, std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector){
   // llvm::errs() << "\n  BO_LE: " <<  opcode << " \n";
  //  exprEvelVector.push_back(std::string() + "(bo_le_rules)" + "==" + "true"); // 
      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "<" +  "(" + RExprStr + ")" + ")" + "||" + "(" +  "(" + LExprStr + ")" + "==" +  "(" + RExprStr + ")" + ")");

      if (const auto *BTR = dyn_cast<BuiltinType>(typeR.getCanonicalType())){
          llvm::errs() << "\n Right Side Kind: " <<  BTR->getKind() << " \n";
          // Add a positive number
          exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "0" + ")"); //a + 0 <= b + 0

          switch (BTR->getKind()) {
            case BuiltinType::Bool:  
              exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  + " && " + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX"); // a <= b + 1
              exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "<=" +  "(" + RExprStr + ")" + " && " +  "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + " >= INT32_MIN"); // a - 1 <= b
              break;

            case BuiltinType::Char_U:
            case BuiltinType::UChar:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a <= b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT8_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;

            case BuiltinType::UShort:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;
            case BuiltinType::UInt:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;
          
            case BuiltinType::ULong:
            case BuiltinType::ULongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" );
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= UINT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;

            
            case BuiltinType::Char_S:
            case BuiltinType::SChar:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a <= b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT8_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;

            case BuiltinType::Short:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"); // a <= b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT16_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;

            case BuiltinType::Int:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" ); // a <= b +1
              ifCondVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT32_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;
            
            case BuiltinType::Long:
            case BuiltinType::LongLong:
              exprEvelVector2.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")"  ); // a <= b + 1
              ifCondVector.push_back( std::string() + "(" + "(" + RExprStr + ")" + "+" + "1" + ")" + " <= INT64_MAX");
              handle_left_type(exprEvelVector,exprEvelVector2, ifCondVector, LExprStr, typeL, RExprStr); // a - 1 <= b
              break;
        
            default:
              break;
          }
      }
      else if (const auto *BTL = dyn_cast<ArrayType>(typeR.getCanonicalType()) ){
        // exprEvelVector.push_back(std::string() + "ARRAY TYPE");
        // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
        exprEvelVector.push_back(std::string() + "(" + LExprStr + ")" + "<=" + "(" + "(" + RExprStr + ")" + "-" + "1" + ")" ); // a <= b -1

      }
      else if  ( const auto *BTL = dyn_cast<PointerType>(typeR.getCanonicalType()) ){
        // exprEvelVector.push_back(std::string() + "POINTER TYPE");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "<=" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "2" + ")" + "==" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");
      }
      else{
        llvm::errs() << "\n Other Kind: " <<  typeR.getCanonicalType() << " \n";
      }

      exprEvelVector.push_back("true");
      // return false;

}


template<typename T>
void bo_ge_rules(std::string exprStr, std::string LExprStr, QualType typeL, std::string RExprStr,QualType typeR, std::vector<T> & exprEvelVector, std::vector<T> & exprEvelVector2, std::vector<T> & ifCondVector){
  // llvm::errs() << "\n  BO_GE: " <<  opcode << " \n";
     
      // "a >= b"   is equal to " b <=  a "
      bo_lt_rules(exprStr, RExprStr, typeR, LExprStr, typeL, exprEvelVector, exprEvelVector2, ifCondVector);
}

template<typename T>
void bo_ne_rules(std::string exprStr, std::string LExprStr, std::string RExprStr,std::vector<T> & exprEvelVector){

  // llvm::errs() << "\n  BO_NE: " <<  opcode << " \n";

      // Fact
      exprEvelVector.push_back(std::string() + "(" + exprStr + ")" + "==" + "true"); // a !- b == true
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "!=" +  "(" + LExprStr + ")" + ")" + "==" + "true"); // b !== a == true

      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "==" +  "(" + RExprStr + ")" + ")" + "==" + "false"); // a == b == false
      exprEvelVector.push_back(std::string() + "(" + "(" + RExprStr + ")" + "==" +  "(" + LExprStr + ")" + ")" + "==" + "false"); // b == a == false

      // // Add a positive number
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "0" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "+" + "0" + ")"); 
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "1" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "+" + "1" + ")");
      // // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "+" + "2" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "+" + "2" + ")");

      // // Add a negative number
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "0" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "-" + "0" + ")");
      exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "1" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "-" + "1" + ")");
      // // exprEvelVector.push_back(std::string() + "(" + "(" + LExprStr + ")" + "-" + "2" + ")" + "!=" + "(" + "(" + RExprStr + ")" + "-" + "2" + ")");


      exprEvelVector.push_back("true");

}
