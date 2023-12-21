#include "stdio.h"
#include <stdbool.h>
#include <stdint.h>

void clang_analyzer_eval(int);

int foo(int a, int b) {
  if ((((void *)0) == (void *)0)) {
    clang_analyzer_eval((((void *)0) == (void *)0) == true);
    clang_analyzer_eval(((((void *)0)) != ((void *)0)) == false);
    clang_analyzer_eval(((((void *)0)) + 0) == (((void *)0) + 0));
    clang_analyzer_eval(((((void *)0)) + 0) < (((void *)0) + 1));
    clang_analyzer_eval(((((void *)0)) - 1) > (((void *)0) - 0));
  }
}