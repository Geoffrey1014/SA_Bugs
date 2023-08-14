#include <stdio.h>
#include <stdint.h>

int main()
{
    int b = 1;
	int *h = &b;
	
	int e = 2;
    int *g[] = {&e, &e};
    
	
	int f = 3;
    int *l = &f;
	int *j = &f;

    for (int d = 0; d <= 1; d++)
    {
        *j = *h && (h = &e);
		//(h = g[d]) && (*j = *h) ;
		//*j = *h;
		//h = g[d];
		printf("*j:%d\n", *j);
		printf("*h:%d\n", *h);
		printf("e:%d\n", e);
		printf("f:%d\n", f);
        // h = g[d];
        //__analyzer_dump ();
    }

    for (int c = 0; c <= 1; c++)
        for (int i = 0; i <= 1; i++)
        {
            int k;
            printf("NPD_FLAG\n");
            k = (*j == *l);
        }
}
