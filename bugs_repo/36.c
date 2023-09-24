#include "stdio.h"
#include <stdint.h>
#include <stdbool.h>
void clang_analyzer_eval(int a){}
int a(); 

uint16_t b() {
  for (;;)
    if (a() <= 0) {
      clang_analyzer_eval((a() <= 0)==true);
      clang_analyzer_eval(((a())<(0))||((a())==(0)));
      clang_analyzer_eval(((a())+0)<=((0)+0));
      clang_analyzer_eval(((a())+0)<=((0)+1));
      clang_analyzer_eval(((a())+1)<=((0)+1));
      clang_analyzer_eval(((a())+0)<=((0)+2));
      clang_analyzer_eval(((a())+1)<=((0)+2));
      clang_analyzer_eval(((a())+2)<=((0)+2));
      clang_analyzer_eval(((a())-0)<=((0)-0));
      clang_analyzer_eval((!(a() <= 0))==false);
      clang_analyzer_eval((((a())>=(0))&&((a())!=(0)))==false);
      clang_analyzer_eval(true);
      ;
    }
}