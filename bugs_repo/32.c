#include "stdio.h"
#include <stdint.h>
#include <stdbool.h>
void clang_analyzer_eval(int){}

int a(int* b, int *c) {
 
d:
  if (c >= b) {
    clang_analyzer_eval((c >= b)==true);
    clang_analyzer_eval(((b)+0)<=((c)+0));
    
    clang_analyzer_eval(((b)-0)<=((c)-0));

    clang_analyzer_eval((!(c >= b))==false);
    clang_analyzer_eval((((c)<=(b))&&((c)!=(b)))==false);
    clang_analyzer_eval(true);
    goto d;
  }
}