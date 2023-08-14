#include "stdint.h"
#include "stdio.h"
#include <stdbool.h>
extern void __analyzer_describe ();
extern void __analyzer_eval ();
extern void __analyzer_dump ();
extern void __analyzer_dump_state ();
extern void __analyzer_dump_region_model ();

void foo (size_t size)
{
  size_t a = size + 2;
  size_t b = size + 1;
  // __analyzer_dump ();
  if(a > b){
    // __analyzer_dump ();
    __analyzer_eval (a > b);
    __analyzer_eval (b < a);
    __analyzer_eval (b > a);
  }
 
}