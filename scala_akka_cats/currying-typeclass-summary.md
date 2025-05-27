# How Currying Enables Type-Class Syntax

## 1. Currying in Scala

**Definition**  
Currying transforms a function taking multiple arguments:
```scala
def f(x: A, y: B): C
```
into a chain of functions each with a single parameter list:
```scala
def f(x: A)(y: B): C
```

**Key consequences**  
1. **Multiple parameter lists**: you can annotate one of them as `implicit`  
2. **Left-to-right type inference**: type parameters are inferred from earlier lists before resolving later ones  

## 2. The Type-Class Pattern in Scala

1. **Type-class trait**  
   ```scala
   trait Show[A] {
     def show(a: A): String
   }
   ```

2. **Implicit instances**  
   ```scala
   implicit val intShow: Show[Int] =
     (a: Int) => s"Int: $$a"
   implicit val stringShow: Show[String] =
     (s: String) => s"String: '$$s'"
   ```

3. **Interface method**  
   ```scala
   def show[A](a: A)(implicit s: Show[A]): String =
     s.show(a)
   ```

## 3. Why Currying Is Essential for Type-Class Syntax

1. **Separation of concerns**  
   - First parameter list (`a: A`) fixes the concrete type `A`.  
   - Second parameter list (`implicit s: Show[A]`) looks up the matching type-class instance.

2. **Type inference flow**  
   - Scala infers `A` from `a: A` in the first list.  
   - Only then does it search for `implicit Show[A]`.

3. **Enabling extension methods via implicit conversions**  
   ```scala
   class ShowOps[A](a: A)(implicit s: Show[A]) {
     def show: String = s.show(a)
   }

   implicit def toShowOps[A](a: A)(implicit s: Show[A]): ShowOps[A] =
     new ShowOps(a)

   // Usage:
   42.show       // → ShowOps(42)(intShow).show
   "hi".show     // → ShowOps("hi")(stringShow).show
   ```

## 4. What Breaks Without Currying

If you write:
```scala
implicit def badOps[A](a: A, s: Show[A]): ShowOps[A] = 
  new ShowOps(a)(s)
```
it fails because:
1. Implicit conversions must have exactly one non-implicit parameter.  
2. Type inference can’t resolve `A` before finding `Show[A]`.

## 5. Recap

- **Implicit parameters** must reside in a separate `implicit` parameter list.  
- **Type inference** operates in stages: first types, then implicits.  
- **Extension-method syntax** (`value.method`) relies on this precise inference and lookup order.
