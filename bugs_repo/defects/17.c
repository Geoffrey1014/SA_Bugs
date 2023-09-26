#include "stdint.h"
#include <stdbool.h>


int a(int* b, int *c) {
 
d:
  if (c >= b) {
    
    __analyzer_eval((!(c >= b))==false);
    __analyzer_eval((((c)<=(b))&&((c)!=(b)))==false);
    __analyzer_eval(true);
    goto d;
  }
}