#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <stdbool.h>
#include <string.h>

#define NONE_LITERAL 42
#define MAX_ALLOCATED_OBJ_COUNT 256
#define MAX_STR_LEN 99999

typedef double float_t;
typedef long long int_t;
typedef char *str_t;
typedef int bool_t;
typedef int none_t;
typedef struct list list_t;
typedef union data data_t;

struct list
{
  data_t *data;
  int_t length;
  int_t uninitialized_length;
};

union data
{
  int_t int_v;
  float_t float_v;
  str_t str_v;
  bool_t bool_v;
  none_t none_v;
  list_t list_v;
};

str_t *allocated_str[MAX_ALLOCATED_OBJ_COUNT];
int allocated_str_count = 0;

list_t *allocated_list[MAX_ALLOCATED_OBJ_COUNT];
int allocated_list_count = 0;

str_t allocate_str(int length)
{
  if (allocated_str_count == MAX_ALLOCATED_OBJ_COUNT)
  {
    printf("Out of memory for string\n");
    exit(1);
  }
  str_t str = (str_t)malloc(length);
  allocated_str[allocated_str_count] = &str;
  allocated_str_count++;
  return str;
}

str_t str_init(char *str)
{
  int_t len = strlen(str);
  str_t new_str = allocate_str(len + 1);
  strcpy(new_str, str);
  return new_str;
}

str_t str_concat(str_t str1, str_t str2)
{
  int_t len1 = strlen(str1);
  int_t len2 = strlen(str2);
  str_t new_str = allocate_str(len1 + len2 + 1);
  strcpy(new_str, str1);
  strcpy(new_str + len1, str2);
  return new_str;
}

void str_clean_up()
{
  for (int i = 0; i < allocated_str_count; i++)
  {
    free(allocated_str[i]);
  }
}

list_t *list_init(int_t length)
{
  list_t *list = malloc(sizeof(data_t));
  list->data = malloc(length * sizeof(void *));
  if (allocated_list_count == MAX_ALLOCATED_OBJ_COUNT)
  {
    printf("Out of memory for list\n");
    exit(1);
  }
  allocated_list[allocated_list_count] = list;
  allocated_list_count++;
  list->length = length;
  list->uninitialized_length = length;
  return list;
}

void list_init_add_internal(list_t *list, data_t value)
{
  if (list->uninitialized_length == 0)
  {
    printf("RUNTIME ERROR: Trying to add more initial elements to full list. Length is %lld\n", list->length);
    exit(1);
  }
  data_t *addr = list->data + list->length - list->uninitialized_length;
  *addr = value;
  list->uninitialized_length--;
}

void list_add_internal(list_t *list, data_t value)
{
  if (list->uninitialized_length != 0)
  {
    printf("RUNTIME ERROR: List initialization is not complete. Length is %lld, uninitialized length is %lld\n", list->length, list->uninitialized_length);
    exit(1);
  }

  list->length++;
  list->data = realloc(list->data, list->length * sizeof(data_t));
  data_t *addr = list->data + list->length - 1;
  *addr = value;
}

void list_free(list_t *list)
{
  if (list == NULL)
    return;
  free(list->data);
  free(list);
}

void list_clean_up()
{
  for (int i = 0; i < allocated_list_count; i++)
  {
    list_free(allocated_list[i]);
  }
}

data_t list_get_internal(list_t *list, int_t index)
{
  if (list->uninitialized_length != 0)
  {
    printf("RUNTIME ERROR: List initialization is not complete. Length is %lld, uninitialized length is %lld\n", list->length, list->uninitialized_length);
    exit(1);
  }
  if (index >= list->length)
  {
    printf("RUNTIME ERROR: Index out of bounds. Trying to access %lld, length is %lld\n", index, list->length);
    exit(1);
  }
  return list->data[index];
}

list_t *list_slice(list_t *list, int_t start, int_t end)
{
  if (list->uninitialized_length != 0)
  {
    printf("RUNTIME ERROR: List initialization is not complete. Length is %lld, uninitialized length is %lld\n", list->length, list->uninitialized_length);
    exit(1);
  }
  if (start < 0 || start >= list->length)
  {
    printf("RUNTIME ERROR: Start index out of bounds. Trying to access %lld, length is %lld\n", start, list->length);
    exit(1);
  }
  if (end < 0 || end >= list->length)
  {
    printf("RUNTIME ERROR: End index out of bounds. Trying to access %lld, length is %lld\n", end, list->length);
    exit(1);
  }
  if (start > end)
  {
    printf("RUNTIME ERROR: Start index is greater than end index. start=%lld, end=%lld\n", start, end);
    exit(1);
  }
  list_t *new_list = list_init(end - start + 1);
  for (int_t i = start; i <= end; i++)
  {
    list_init_add_internal(new_list, list->data[i]);
  }
  return new_list;
}

void input_helper_invalid_input()
{
  int c;
  while ((c = getchar()) != EOF && c != '\n')
    continue;
  if (c == EOF)
  {
    printf("RUNTIME ERROR: Reaching unexpected EOF.\n");
    exit(1);
  }
  printf("Invalid input. Please try again.\n");
}

data_t input_internal(char *prompt, char type)
{
  data_t value;
start:
  printf("%s", prompt);
  switch (type)
  {
  // https://stackoverflow.com/questions/40551037/scanf-not-working-on-invalid-input
  case 'i':
    printf(" (expecting int): ");
    if (scanf("%lld", &value.int_v) != 1)
    {
      input_helper_invalid_input();
      goto start;
    }
    break;
  case 'f':
    printf(" (expecting float): ");
    if (scanf("%lf", &value.float_v) != 1)
    {
      input_helper_invalid_input();
      goto start;
    }
    break;
  case 's':
    printf(" (expecting string): ");
    char str_tmp[MAX_STR_LEN];
    if (scanf("%s", str_tmp) != 1)
    {
      input_helper_invalid_input();
      goto start;
    }
    value.str_v = str_init(str_tmp);
    break;
  case 'b':
    printf(" (expecting bool): ");
    if (scanf("%d", &value.bool_v) != 1)
    {
      input_helper_invalid_input();
      goto start;
    }
    break;
  default:
    printf("RUNTIME ERROR: Unknown type %c\n", type);
    exit(1);
  }

  return value;
}

int print_internal(int items_count, ...)
{
  va_list valist;
  va_start(valist, items_count);

  for (int i = 0; i < items_count; i++)
  {
    char type = va_arg(valist, /* str_t */ int);
    switch (type)
    {
    case 'i':
      printf("%lld", va_arg(valist, int_t));
      break;
    case 'f':
      printf("%lf", va_arg(valist, float_t));
      break;
    case 'c':
      printf("%c", va_arg(valist, /* str_t */ int));
      break;
    case 'b':
      printf("%s", va_arg(valist, bool_t) ? "true" : "false");
      break;
    case 's':
      printf("%s", va_arg(valist, char *));
      break;
    default:
      printf("RUNTIME ERROR: Unknown type: %c\n", type);
      exit(1);
    }
    printf(" ");
  }
  printf("\n");
  va_end(valist);
  return 0;
}

#define list_get(vname, list, index) \
  list_get_internal(list, index).vname

#define list_init_add(vname, list, value) \
  list_init_add_internal(list, (data_t){.vname = value})

#define list_add(vname, list, value) \
  list_add_internal(list, (data_t){.vname = value})

#define input(vname, prompt) \
  input_internal(prompt, #vname[0]).vname

#define input_int() input(int_v, "Enter a number")
#define input_float() input(float_v, "Enter a number")
#define input_bool() input(int_v, "Enter 0 or 1")
#define input_str() input(str_v, "Enter a string")

#define input_int_s(X) input(int_v, X)
#define input_float_s(X) input(float_v, X)
#define input_bool_s(X) input(int_v, X)
#define input_str_s(X) input(str_v, X)

#define print_int(X) print_internal(1, 'i', X)
#define print_float(X) print_internal(1, 'f', X)
#define print_bool(X) print_internal(1, 'b', X)
#define print_str(X) print_internal(1, 's', X)
