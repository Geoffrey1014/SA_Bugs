unsigned int func(unsigned int a) {
	unsigned int *z = 0;

	if ((a & 1) && ((a & 1) ^1))
		return *z; // unreachable

	return 0;
}
