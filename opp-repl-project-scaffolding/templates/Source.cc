// Template: skeleton simple module implementation.
//
// Must declare `Define_Module(Source)` inside any namespace that
// matches the NED package declaration (see Source.h).

#include "Source.h"

// namespace mm1k {   // <- uncomment to match Source.h and Network.ned

Define_Module(Source);

void Source::initialize()
{
    scheduleAt(simTime() + 1.0, new cMessage("tick"));
}

void Source::handleMessage(cMessage *msg)
{
    send(msg, "out");
    scheduleAt(simTime() + 1.0, new cMessage("tick"));
}

// }   // namespace mm1k
