#include <stdio.h>
void a( int *d  , int* e) { 
  printf("NPD_FLAG\n");
  e == 0 && (d = 0) != *e; // *f  result in npd
}
int main() {
    int i =5;
    a(0 ,&i);
}