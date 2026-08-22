# C# Fallback Skeleton

> **Priority:** Optional
> **Est. time:** 20 min
> **Track:** Both
> **HelloInterview:** none

A minimal `dotnet new console` equivalent of this project's Python skeleton — the second
fallback, behind [SCALA.md](SCALA.md), for a language-agnostic laptop round. Deliberately
short: enough to be usable if it comes to it, not a second full harness. The Python skeleton in
this directory is still the primary plan.

---

## 1 · Setup — do this once, ahead of time

```bash
dotnet new console -o solution
cd solution
dotnet run          # first run restores/builds — this is the network/cold-start risk
```
The first `dotnet run` after `dotnet new` triggers a NuGet restore and build; if the SDK's
reference packages aren't already cached locally, this can take a while on a cold machine. Run
it once well before interview day so the local cache is warm — the same principle as
`scala-cli`'s first-run cache warm in [SCALA.md](SCALA.md).

If your installed SDK is recent enough to support **file-based apps** (`dotnet run Program.cs`
directly, no `.csproj` at all — check `dotnet --version`, this landed as a supported feature
in .NET 10), that's an even smaller-surface alternative worth verifying ahead of time too.
`dotnet new console` below is the safe, universally-supported default.

## 2 · The skeleton

`Program.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

// Worked example: sum whitespace-separated integers per line. Replace Solve's body,
// keep the signature — same streaming, args-in/lines-out shape as the Python harness.
static IEnumerable<string> Solve(IEnumerable<string> lines)
{
    foreach (var line in lines)
    {
        var nums = line.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries)
                        .Select(int.Parse);
        yield return nums.Sum().ToString();
    }
}

static IEnumerable<string> ReadAllLines(TextReader reader)
{
    string? line;
    while ((line = reader.ReadLine()) is not null)
        yield return line;
}

static void Check(string name, object actual, object expected)
{
    if (Equals(actual, expected)) Console.Error.WriteLine($"OK   {name}");
    else
    {
        Console.Error.WriteLine($"FAIL {name}: expected {expected}, got {actual}");
        Environment.Exit(1);
    }
}

static void RunTests()
{
    Check("sum basic", Solve(new[] { "1 2 3" }).First(), "6");
    Check("multi line", string.Join(",", Solve(new[] { "1 2", "3 4" })), "3,7");
    Console.Error.WriteLine("all tests passed");
}

// --- entry point: everything above is declarations; this is the only executed code ---

if (args.Contains("--test"))
{
    RunTests();
    return;
}

var inputIndex = Array.IndexOf(args, "--input");
using TextReader input = inputIndex >= 0 && inputIndex + 1 < args.Length
    ? new StreamReader(args[inputIndex + 1])
    : Console.In;

foreach (var result in Solve(ReadAllLines(input)))
    Console.WriteLine(result);
```

Run it:
```bash
printf '1 2 3\n4 5\n' | dotnet run                 # stdin -> stdout
dotnet run -- --input in.txt                        # file -> stdout
dotnet run -- --test                                # runs the hand-rolled checks, no xUnit/NUnit
```

## 3 · Minimal tests, no framework

`dotnet new xunit`/`dotnet new nunit` are a **second** project plus their own package restore —
another cold-start risk on top of the console project's own. The `--test` flag above avoids
that entirely: no second project, no additional NuGet restore, same executable either way.

---

## Interview questions

**Why `dotnet new console` over a full ASP.NET or test-framework project template?**
Smallest possible surface and fewest packages to restore — matches the round's "no heavy
frameworks" grading note, and there's no second project's cold start to warm ahead of time.

**What's the cold-start risk with `dotnet new console`, and how do you avoid it?**
The first `dotnet run` after creating the project triggers a NuGet restore and build; if the
SDK's packages aren't cached locally yet, that costs real time. Run it once, well before
interview day, so the local cache is already warm.

**How do you run tests here without an xUnit or NUnit project?**
A hand-rolled `Check(name, actual, expected)` helper gated behind a `--test` argument inside
the same `Program.cs` — no second project, no extra package restore, same binary either way.

**How would you wire this to read from a file instead of stdin?**
Look for an `--input` flag in `args` for a path and choose between `new StreamReader(path)` and
`Console.In` — the same resolve-input-by-channel shape as the Python harness's
`resolve_input()`.

**What's the "file-based app" feature in recent .NET SDKs, and why mention it here?**
`dotnet run Program.cs` directly, with no `.csproj` at all, on SDKs that support it (a
supported feature since .NET 10) — an even smaller setup than `dotnet new console`. Worth
checking `dotnet --version` ahead of time; `dotnet new console` above is the safe fallback if
it's unavailable.
