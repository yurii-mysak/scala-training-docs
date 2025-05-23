# Advanced SBT Usage

This chapter aggregates our 2024‑05‑08, 2024‑11‑11, and 2025‑03 chats on **multi‑project builds**, **plugins**, **assembly vs native‑packager**, and advanced task customisation.

---

## 1. Multi‑project build

`project/build.sbt`

```scala
lazy val root = (project in file("."))
  .aggregate(api, core)
  .settings(name := "my-root")

lazy val core = (project in file("core"))
lazy val api  = (project in file("api"))
  .dependsOn(core)
```

* `aggregate` triggers sub‑project tasks when run from root.  
* Use `dependsOn` to add classpath dependency.

### 1.1 Command‑line targeting
```
sbt> core/test
sbt> api/compile
```

---

## 2. Plugins buffet

| Plugin | Purpose |
|--------|---------|
| `sbt-assembly` | Fat JAR packaging (`assembly` task) |
| `sbt-native-packager` | Docker, rpm, deb bundles |
| `sbt-updates` | `dependencyUpdates` |
| `sbt-dependency-graph` | `dependencyTree` |
| `sbt-sonatype` + `pgp` | OSS publishing to Maven Central |

`project/plugins.sbt`
```scala
addSbtPlugin("com.eed3si9n"  % "sbt-assembly"         % "2.2.0")
addSbtPlugin("com.github.sbt" % "sbt-native-packager" % "1.10.0")
```

---

## 3. Assembly vs Native‑Packager

| | **assembly** | **native‑packager** |
|---|-------------|--------------------|
| Output | Single shaded JAR | Docker image, rpm, etc. |
| Merge strategy | Need to deduplicate resources | Handles via stages |
| Use case | Lambda, simple fatjar deploy | Container or system pkg |

Chat 2025‑04‑06: we chose assembly for AWS Lambda runtime due to cold‑start size.

---

## 4. Dependency tree & eviction rules
```shell
sbt> dependencyTree
sbt> evictionRules
```
Add in CI to fail on unexpected downgrades.

---

## 5. Publishing artifacts

```scala
ThisBuild / organization := "com.example"
publishTo := sonatypePublishTo.value
```
Run:
```
sbt +clean +publishSigned sonatypeBundleRelease
```
The `+` prefix cross‑publishes (see §6).

---

## 6. Cross builds
```scala
ThisBuild / crossScalaVersions := Seq("2.13.14","3.6.0")
```
Matrix in GitHub Actions:
```yaml
strategy:
  matrix:
    scala: [2.13.14, 3.6.0]
```

---

## 7. Custom settings & tasks
```scala
lazy val apiEndpoint = settingKey[String]("Prod API URL")

Compile / resourceGenerators += Def.task {
  val file = (Compile / resourceManaged).value / "endpoint.conf"
  IO.write(file, s"url=${apiEndpoint.value}")
  Seq(file)
}
```
Demonstrated during 2024‑11‑11 docker‑conf injection.

---

## 8. Command‑line reference (hand‑picked)
| Command | Effect |
|---------|--------|
| `projects` | list sub‑projects |
| `reload` | re‑evaluate build definitions |
| `show fullClasspath` | inspect classpath |
| `~testQuick` | watch mode |
| `last compile` | show previous task log |

---

## 9. Native‑packager Docker quickstart
```scala
enablePlugins(JavaAppPackaging, DockerPlugin)
Docker / maintainer := "Yuriy"
```
`docker:publishLocal` builds image.

---

## 10. Interview checklist
* Difference between `assembly` and `packageBin`.  
* How `dependsOn` vs `aggregate` impacts transitive classpath.  
* Publishing flow to Maven Central.
