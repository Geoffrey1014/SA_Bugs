#include <stdio.h>
#include <string.h>
void __analyzer_describe ();
 void __analyzer_eval (int a){};
 void __analyzer_dump ();

int main() { 
  int *j = 0;
  
  int a = printf("NPD_FLAG\n") ;
  __analyzer_describe(0,a);
  a || *j;

  int b = strlen("NPD_FLAG\n");
  b || *j;
  __analyzer_describe(0,b);


  char arr1[] = "abcdefghi";
	char arr2[] = "bit";
	strcpy(arr1, arr2);//字符串拷贝

}
