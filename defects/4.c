#include "stdio.h"
#include <stdbool.h>
#include <stdint.h>

void clang_analyzer_eval(int) {}

int a(int *b, int *c) {
d:
  if (c >= b) {
    clang_analyzer_eval((c >= b) == true);
    clang_analyzer_eval(((b) + 0) <= ((c) + 0));
    clang_analyzer_eval(((b)-0) <= ((c)-0));
    clang_analyzer_eval((!(c >= b)) == false);
    clang_analyzer_eval((((c) <= (b)) && ((c) != (b))) == false);
    goto d;
  }
}