
void __analyzer_describe(){};
#include <stdio.h>
void __analyzer_eval(int a){
    printf("world %d", a);
};
void c()
{
    int d = 42;
    int *e = &d;

    if (e == &d)
    {
        printf("hello\n");

        // __analyzer_describe(0, e);
        // __analyzer_describe(0, &d + 1);

        __analyzer_eval(e == &d + 2);
        // __analyzer_eval(e + 1 == &d + 1);
    }
}
int main(){
    c();
}