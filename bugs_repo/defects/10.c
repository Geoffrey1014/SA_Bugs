#include "stdio.h"
void clang_analyzer_eval(int);
void clang_analyzer_warnIfReached();
int *f(int *);

int *f(int *p)
{
    p = (int *)0;
    return p;
}

int main()
{
    int a = 42;
    int *p = &a;
    clang_analyzer_eval(0 == p);
    p = f(p);
    clang_analyzer_eval(0 == p);
    if (p == (int *)0)
    {
        clang_analyzer_eval(0 == p);
        *p = 42;
    }
}