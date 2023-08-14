
int main() {
	int *b = (void *)0;
	if (b == 0) {
		// clang_analyzer_eval(b==0); // TRUE
		// clang_analyzer_eval((b+1)==(0+1)); // TRUE
		int *p = (void *)0;
		if (b + 1 != 1) { // b+1 is not UB 
			*p = 100;
		}
	}
    return 0;
}