#include "stdint.h"
#include <stdbool.h>
int a(); 

uint16_t b() {
    for(;;)
    if (a() <= 0) {
      __analyzer_eval((a() <= 0)==true);
      __analyzer_eval(((a())<(0))||((a())==(0)));
      __analyzer_eval(((a())+0)<=((0)+0));
      __analyzer_eval(((a())+0)<=((0)+1));
      __analyzer_eval(((a())+1)<=((0)+1));
      __analyzer_eval(((a())+0)<=((0)+2));
      __analyzer_eval(((a())+1)<=((0)+2));
      __analyzer_eval(((a())+2)<=((0)+2));
      __analyzer_eval(((a())-0)<=((0)-0));
      __analyzer_eval((!(a() <= 0))==false);
      __analyzer_eval((((a())>=(0))&&((a())!=(0)))==false);
      __analyzer_eval(true);
      ;
    }
}