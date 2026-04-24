// Template: skeleton simple module header.
//
// IMPORTANT NAMESPACE RULE:
// If you wrap in `namespace mm1k { ... }`, the registered class name
// becomes `mm1k::Source`.  Your .ned file MUST then declare
// `package mm1k;` so the NED type `Source` resolves to `mm1k::Source`.

#ifndef __SOURCE_H
#define __SOURCE_H

#include <omnetpp.h>

using namespace omnetpp;

// namespace mm1k {   // <- uncomment together with Source.cc + Network.ned

class Source : public cSimpleModule
{
  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
};

// }   // namespace mm1k

#endif
