#include <stdio.h>
int l ;

int *b( int *n) {
  for (; l < 3;)
    return n;
}

int d() {
  int f;
  int *g = &f;
  int *i;
  (i = b(g)) || 1; //instrument_npd103.c:12:4: note: Assuming 'i' is null,  removing "|| 1" would change analysis result;
  printf("NPD_FLAG\n");
  *i;
}

void main() { d(); }
