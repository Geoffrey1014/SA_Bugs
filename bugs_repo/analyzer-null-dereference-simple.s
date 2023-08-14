	.file	"analyzer-null-dereference-simple.c"
	.text
	.p2align 4
	.globl	fix_overlays_before
	.type	fix_overlays_before, @function
fix_overlays_before:
.LFB7:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$8, %rsp
	.cfi_def_cfa_offset 64
	movq	(%rdi), %rbx
	testq	%rbx, %rbx
	je	.L1
	movq	%rdi, %r14
	movq	%rsi, %r13
	movq	%rdx, %rbp
	xorl	%r12d, %r12d
	jmp	.L2
	.p2align 4,,10
	.p2align 3
.L4:
	movq	16(%rbx), %rax
	movq	%rbx, %r12
	testq	%rax, %rax
	je	.L1
	movq	%rax, %rbx
.L2:
	movq	8(%rbx), %rdi
	call	marker_position
	cmpq	%rbp, %rax
	jge	.L4
	cmpq	%r13, %rax
	jl	.L1
	movq	16(%rbx), %r15
.L21:
	testq	%r15, %r15
	je	.L1
.L24:
	movq	8(%r15), %rdi
	call	marker_position
	cmpq	%rax, %rbp
	je	.L23
	cmpq	%rax, %r13
	jne	.L1
	movq	%r15, %rbx
	movq	16(%r15), %r15
	testq	%r15, %r15
	jne	.L24
.L1:
	addq	$8, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
	.p2align 4,,10
	.p2align 3
.L23:
	.cfi_restore_state
	movq	16(%r15), %rax
	movq	%rax, 16(%rbx)
	testq	%r12, %r12
	je	.L25
	movq	16(%r12), %rdx
	movq	%rdx, 16(%r15)
	movq	%r15, 16(%r12)
.L7:
	movq	%rax, %r15
	jmp	.L21
	.p2align 4,,10
	.p2align 3
.L25:
	movq	(%r14), %rdx
	movq	%rdx, 16(%r15)
	movq	%r15, (%r14)
	jmp	.L7
	.cfi_endproc
.LFE7:
	.size	fix_overlays_before, .-fix_overlays_before
	.ident	"GCC: (GNU) 13.0.0 20221104 (experimental)"
	.section	.note.GNU-stack,"",@progbits
