#include <assert.h>
#include <stdbool.h>
extern void __analyzer_eval (int);

void decode(int width) {
//   assert(width > 0);
if (width > 0){
  int base;
  bool inited = false;

  int i = 0;
  if (i - width < 0) {
    base = 512;
    inited = true;
  }
//   assert(inited); // <- if i uncomment this, the warning is gone.
  base+=1;

  if (base >> 10)
    assert(false);
}
}