#include <assert.h>
#include <stdbool.h>
extern void __analyzer_eval (int);

void decode(int a) {
if (a > 0){
  int c;
  bool d = false;

  int i = 0;
  if (i - a < 0) {
    c = 512;
    d = true;
  }
  c+=1;

  if (c >> 10)
    assert(false);
}
}