#include "stdio.h"
#include <stdint.h>
#include <stdbool.h>

void clang_analyzer_eval();

int32_t a(int8_t b) {
  if (255UL == b) {
    clang_analyzer_eval((255UL == b));
    clang_analyzer_eval((255UL == b)==true);
    clang_analyzer_eval(((255UL)!=(b))==false);
    clang_analyzer_eval(((255UL)+0)==((b)+0));
    clang_analyzer_eval(((255UL)-0)==((b)-0));
    
  }
}