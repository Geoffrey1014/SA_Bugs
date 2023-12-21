#include <stdbool.h>
#include <stdint.h>

void clang_analyzer_eval();

int foo(int a, int b) {
  if ((a < b) && (0 < a)) {
    clang_analyzer_eval(!(a < b) == false);
    clang_analyzer_eval(b > 0);
  }
}