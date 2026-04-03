# Scala Language

Core Scala syntax, type system, collections, implicits, and metaprogramming.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | Collections | [Collections.md](Collections.md) | Immutable vs mutable, performance characteristics |
| 2 | Option type | [Option.md](Option.md) | Null safety, Option vs null, map/flatMap/getOrElse |
| 3 | Pattern matching | [PatternMatching.md](PatternMatching.md) | Match expressions, case classes, guards, sealed traits |
| 4 | Objects & companions | [ObjectsCompanions.md](ObjectsCompanions.md) | Singleton, apply/unapply, companion object patterns |
| 5 | Traits vs classes | [TraitsClasses.md](TraitsClasses.md) | Linearization, stackable traits, diamond problem |
| 6 | For-comprehensions | [ForComprehensions.md](ForComprehensions.md) | Desugaring to map/flatMap/withFilter |
| 7 | Generic classes | [GenericClasses.md](GenericClasses.md) | Type parameters, bounds, variance basics |
| 8 | Type hierarchy | [TypeHierarchy.md](TypeHierarchy.md) | Any, AnyVal, AnyRef, Nothing, Null |
| 9 | Value types & boxing | [scala_value_types_boxing.md](scala_value_types_boxing.md) | AnyVal, boxing/unboxing, performance implications |

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 10 | Advanced functions | [AdvancedFunctions.md](AdvancedFunctions.md) | Higher-order functions, currying, partial application |
| 11 | Implicits & type classes | [ImplicitsTypeClasses.md](ImplicitsTypeClasses.md) | Implicit conversions, parameters, resolution rules |
| 12 | Currying & type classes | [currying-typeclass-summary.md](currying-typeclass-summary.md) | Currying mechanics, type class pattern |
| 13 | SBT advanced | [SBT_Advanced.md](SBT_Advanced.md) | Multi-project builds, plugins, custom tasks |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 14 | Advanced type system | [Advanced-TypeSystem.md](Advanced-TypeSystem.md) | Path-dependent types, type members, structural types |
| 15 | Type class hierarchy | [typeclass_hierarchy.md](typeclass_hierarchy.md) | Functor, Applicative, Monad hierarchy |
| 16 | Type classes & category theory | [Type-Classes-and-CT.md](Type-Classes-and-CT.md) | Monoid, Semigroup, Functor laws |
| 17 | Shapeless & HLists | [Shapeless_HLists.md](Shapeless_HLists.md) | Generic programming, type-level computation |
| 18 | Macros & metaprogramming | [MacrosMeta.md](MacrosMeta.md) | Compile-time code generation, reflection |

## Key Interview Questions by Level

**Beginner**: What is the difference between `val`, `var`, and `def`? How does pattern matching work with sealed traits? Why prefer immutable collections?

**Intermediate**: Explain implicit resolution order. How does currying enable type inference? What are context bounds?

**Advanced**: How do path-dependent types work? Explain the relationship between Functor, Applicative, and Monad. When would you use shapeless?
