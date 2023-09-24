#include <stdio.h>
int a()
{
    for (int d = -2; d; ++d){
        ;
    }
    // int * p = d;
    // printf("%d",*p);  // pinpoint report this NPD
    return d;
}

int b()
{
  
    int t = a();
    int *c = (void *)t;
    printf("%d",*c);  // pinpoint does not report this NPD
}

int main() { b(); }
