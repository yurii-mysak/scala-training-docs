# Linearizability vs Serializability

## Definitions

- **Linearizability**: Ensures each individual operation appears instantaneous at some real-time point between its start and end.
- **Serializability**: Ensures transactions appear to execute sequentially, preserving consistency and isolation without strict real-time adherence.

## Scope of Application

| Linearizability                                | Serializability                                     |
|------------------------------------------------|-----------------------------------------------------|
| Single operations (e.g., reads/writes)         | Transactions                                        |
| Strict real-time appearance                    | Logical sequential appearance                       |

## Consistency Model

| Linearizability                                | Serializability                                     |
|------------------------------------------------|-----------------------------------------------------|
| Strongest consistency guarantee                | Transactional consistency, slightly weaker          |
| Strictly maintains real-time ordering          | Does not strictly maintain real-time ordering       |

## Use Cases and Examples

### Linearizability
- Distributed locking mechanisms
- Coordination services like etcd, ZooKeeper

### Serializability
- Database transaction management
- Financial systems, e.g., account transfers

## Latency & Performance

| Linearizability                                | Serializability                                     |
|------------------------------------------------|-----------------------------------------------------|
| Higher latency due to strict synchronization   | Lower latency due to concurrency optimizations      |
| Limited parallelism                            | Greater potential parallelism                       |

## Guarantees Provided

| Linearizability                                | Serializability                                     |
|------------------------------------------------|-----------------------------------------------------|
| Immediate real-time visibility                 | Transactional consistency without immediate real-time visibility |
| Each operation strictly ordered                | Transactions logically ordered                      |

## Comparison Summary

| Criteria                 | Linearizability                  | Serializability                        |
|--------------------------|----------------------------------|----------------------------------------|
| Consistency strength     | Strongest                        | Slightly weaker                        |
| Scope                    | Operations                       | Transactions                           |
| Real-time requirement    | Yes                              | No                                     |
| Performance & Latency    | Higher latency                   | Lower latency                          |
| Implementation complexity| Higher                           | Moderate                               |

## Quick Analogy

- **Linearizability**: Single queue at a checkout line—strict real-time order.
- **Serializability**: Multiple checkout lanes—transactions appear ordered but not strictly by real-time arrival.

## Conclusion

- Choose **Linearizability** when exact real-time operation order is critical.
- Choose **Serializability** when transactional consistency matters, without strict real-time ordering.
