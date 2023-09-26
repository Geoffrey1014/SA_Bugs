#include <stdint.h>
#include <stdbool.h>

int main(int a, int b, int c, int d) {
    if ((a<b) && (a>0)){
        __analyzer_eval(!(a<b) == false); 
        __analyzer_eval(b > 0);

    }
}
