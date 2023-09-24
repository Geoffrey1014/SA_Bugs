#include <stdio.h>
int b( int *p) {
  int n=2;
  printf("reach NPD\n");
  *p = n;
  return 1;
}


int main() {
  int g, h;
  for (int i =0;;i++) {
    int j=1;
    int *k[2][7];
    for (g = 0; g < 2; g++)
      for (h = 0; h < 7; h++)
        k[g][h] = &j;
    if (b(k[1][0])){
        k[1][0] = 0;
        printf("reach k\n");
    }
      if (i)
        break;
  }
}

// k[1][0], k[1][1] : FP
// k[0][0], k[0][1] : no FP