#include <stdint.h>
#include <stdbool.h>

int main(int a, int b, int c, int d) {
    if ((a<b)){
        //Negation
        __analyzer_eval(!(a<b) == false); 
        __analyzer_eval(-a > -b);

        // Add a positive number after the negation
        __analyzer_eval(0-a > 0-b);
        __analyzer_eval(1-a > 0-b);
        __analyzer_eval(1-a > 1-b);
        __analyzer_eval(2-a > 0-b);
        __analyzer_eval(2-a > 1-b);
        __analyzer_eval(2-a > 2-b);

        // Add a negative number after the negation
        __analyzer_eval(-0-a > -0-b);
        __analyzer_eval(-1-a > -0-b);
        __analyzer_eval(-1-a > -1-b);
        __analyzer_eval(-2-a > -0-b);
        __analyzer_eval(-2-a > -1-b);
        __analyzer_eval(-2-a > -2-b);

        //Multiply the positive number after the negation
        __analyzer_eval( -a*0 == -b*0);
        __analyzer_eval( -a*1 > -b*1);
        __analyzer_eval( -a*2 > -b*2);
        __analyzer_eval( -a*3 > -b*3);

        //Multiply the negative number after the negation
        __analyzer_eval( -1*-a < -1*-b);
        __analyzer_eval( -2*-a < -2*-b);
        __analyzer_eval( -3*-a < -3*-b);
    }
}
