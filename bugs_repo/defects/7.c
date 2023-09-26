#include <stdint.h>
#include <stdbool.h>

int main(int a, int b, int c, int d) {
    if ((a>b)){
        __analyzer_eval(a>b);
        __analyzer_eval(!(a>b) == false);
        __analyzer_eval(-a < -b);
        __analyzer_eval(0-a < 0-b);
        __analyzer_eval( a+0 > b+0);
        __analyzer_eval( a+1 > b+1);
        __analyzer_eval( a+2 > b+2);
        __analyzer_eval( a+2 > b+1);
        __analyzer_eval( a+3 > b+1);
    }
}