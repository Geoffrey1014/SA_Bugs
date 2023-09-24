#include "stdio.h"
int f(int, int *);

int f(int p, int *q)
{
    __analyzer_eval(p && 0 == q);
    if (p && (0 == q))
    {
        __analyzer_eval(p && (0 == q));
        __analyzer_eval(p);
        __analyzer_eval(q);
        __analyzer_eval(0 == q);
        *q = 1;
    }
    printf("NPD_FLAG\n");
}

int main()
{
    int a = 0;
    int *b = (void *)0;
    f(a, b);
}
