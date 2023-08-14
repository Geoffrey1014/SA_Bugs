struct lisp;
union vectorlike_header { long size; };

static struct lisp *
make_lisp_ptr (void *ptr, int type)
{
  char *p = ptr;
  void *q = p + type;
  return q;
}

static _Bool
TAGGEDP (struct lisp *a, unsigned tag)
{
  return ! (((unsigned) (long) a - tag) & 7);
}

static _Bool
VECTORLIKEP (struct lisp *x)
{
  return TAGGEDP (x, 5);
}

static _Bool
PSEUDOVECTOR_TYPEP (union vectorlike_header const *a, int code)
{
  long PSEUDOVECTOR_FLAG = 1L << 62;
  long PVEC_TYPE_MASK = 0x3fL << 24;
  return ((a->size & (PSEUDOVECTOR_FLAG | PVEC_TYPE_MASK))
	  == (PSEUDOVECTOR_FLAG | (code << 24)));
}

static _Bool
PSEUDOVECTORP (struct lisp *a, int code)
{
  if (! VECTORLIKEP (a))
    return 0;
  else
    return PSEUDOVECTOR_TYPEP ((union vectorlike_header *) ((char *) a - 5),
			       code);
}

struct Lisp_Overlay
{
  union vectorlike_header header;
  struct lisp *end;
  struct Lisp_Overlay *next;
};

static _Bool
OVERLAYP (struct lisp *x)
{
  return PSEUDOVECTORP (x, 4);
}

static struct Lisp_Overlay *
XOVERLAY (struct lisp *a)
{
  void *r = (char *) a - 5;
  return r;
}
struct buffer { struct Lisp_Overlay *overlays_before; };

long marker_position (struct lisp *);

void
fix_overlays_before (struct buffer *bp, long prev, long pos)
{
  struct Lisp_Overlay *tail = bp->overlays_before, *parent = 0, *right_pair;
  struct lisp *tem;
  long end;
  while (tail
	 && (tem = make_lisp_ptr (tail, 5),
	     (end = marker_position (XOVERLAY (tem)->end)) >= pos))
    {
      parent = tail;
      tail = tail->next;
    }
  if (!tail || end < prev || !tail->next)
    return;
  right_pair = parent;
  parent = tail;
  tail = tail->next;
  while (tail)
    {
      tem = make_lisp_ptr (tail, 5);
      end = marker_position (XOVERLAY (tem)->end);
      if (end == pos)
	{
	  struct Lisp_Overlay *found = tail;
	  tail = found->next;
	  parent->next = tail;
	  if (!right_pair)
	    {
	      found->next = bp->overlays_before;
	      bp->overlays_before = found;
	    }
	  else
	    {
	      found->next = right_pair->next;
	      right_pair->next = found;
	    }
	}
      else if (end == prev)
	{
	  parent = tail;
	  tail = tail->next;
	}
      else
	break;
    }
}