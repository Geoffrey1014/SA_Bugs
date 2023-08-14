#include "stdio.h"
 void __analyzer_describe (int a){};
 void __analyzer_eval (int a){};
 void __analyzer_dump ();

void foo(int* c )
{
    int** p = &c;
    unsigned long a = (unsigned long) p;
    int **b = (int **)a;
    // __analyzer_dump ();
    // __analyzer_eval (a == 0);
    // __analyzer_describe(0,a);

    if(0 == c){        
        __analyzer_eval (b == a);
        __analyzer_eval (p == a);
        __analyzer_eval (b == p);

        __analyzer_eval (b == 0);
        
        __analyzer_eval (a == &c);
        **b = 1;
        // **(int**)a = 1;
        // __analyzer_describe(0,**b);
        // __analyzer_dump ();
    }
}
int main(){
    foo(0);
    return 0;
}