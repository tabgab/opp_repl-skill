// Template: minimal NED network skeleton.
//
// IMPORTANT: if your .cc files use `namespace mm1k { ... }` then you
// MUST add `package mm1k;` as the FIRST line of every .ned file in
// this project.  Either both have a package/namespace, or neither.

// package mm1k;    // <- uncomment if your C++ uses `namespace mm1k { }`

simple Source
{
    parameters:
        @display("i=block/source");
    gates:
        output out;
}

simple Sink
{
    parameters:
        @display("i=block/sink");
    gates:
        input in;
}

network Network
{
    submodules:
        src: Source;
        snk: Sink;
    connections:
        src.out --> snk.in;
}
