#include <stdio.h>
#include <string.h>

long func(int a){
    long sum = 0;
    for(int j=1;j<=a;j++){
    	sum += j;
    }
    return sum;
}

int main(void){
    int a =100;
    
    printf("%ld",a);
    long sum = func(a);
    printf("%ld",sum);
    int b = strlen("Hello\n");
    printf("%ld",b);
    return 0;
}
