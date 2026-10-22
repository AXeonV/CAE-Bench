// Trusted adapter: call the unmodified public Chrono API on supplied states.
// This file supplies no reference acceleration or reaction calculation.
#include <iomanip>
#include <iostream>
#include <memory>
#include <vector>
#include "chrono/physics/ChBody.h"
#include "chrono/physics/ChLinkDistance.h"
#include "chrono/physics/ChSystemNSC.h"
#include "chrono/timestepper/ChAssemblyAnalysis.h"

using namespace chrono;

ChVector3d ReadVector() {
    double x, y, z;
    if (!(std::cin >> x >> y >> z)) throw std::runtime_error("Invalid vector");
    return ChVector3d(x, y, z);
}

void WriteVector(const ChVector3d& v) {
    std::cout << '[' << v.x() << ',' << v.y() << ',' << v.z() << ']';
}

int main() {
    try {
        int n, m, action;
        if (!(std::cin >> n >> m >> action) || n < 1 || n > 32 || m < 0 || m > 32)
            throw std::runtime_error("Invalid dimensions");
        ChSystemNSC system;
        system.SetSolverType(ChSolver::Type::SPARSE_QR);
        system.SetGravitationalAcceleration(ReadVector());
        std::vector<std::shared_ptr<ChBody>> bodies;
        for (int i = 0; i < n; ++i) {
            double mass;
            int fixed;
            if (!(std::cin >> mass >> fixed)) throw std::runtime_error("Invalid body");
            auto body = chrono_types::make_shared<ChBody>();
            body->SetMass(mass);
            body->SetFixed(fixed != 0);
            body->SetInertiaXX(ChVector3d(1, 1, 1));
            body->SetPos(ReadVector());
            body->SetPosDt(ReadVector());
            auto force = ReadVector();
            auto accumulator = body->AddAccumulator();
            body->AccumulateForce(accumulator, force, body->GetPos(), false);
            system.Add(body);
            bodies.push_back(body);
        }
        std::vector<std::shared_ptr<ChLinkDistance>> links;
        for (int i = 0; i < m; ++i) {
            int a, b;
            double length;
            if (!(std::cin >> a >> b >> length) || a < 0 || b < 0 || a >= n || b >= n)
                throw std::runtime_error("Invalid link");
            auto link = chrono_types::make_shared<ChLinkDistance>();
            link->Initialize(bodies[a], bodies[b], true, ChVector3d(0, 0, 0),
                             ChVector3d(0, 0, 0), false, length);
            system.AddLink(link);
            links.push_back(link);
        }
        auto result = system.DoAssembly(action);
        if (result == AssemblyAnalysis::ExitFlag::NOT_CONVERGED)
            throw std::runtime_error("Assembly did not converge");
        std::cout << std::setprecision(17) << "{\"position\":[";
        for (int i = 0; i < n; ++i) { if (i) std::cout << ','; WriteVector(bodies[i]->GetPos()); }
        std::cout << "],\"velocity\":[";
        for (int i = 0; i < n; ++i) { if (i) std::cout << ','; WriteVector(bodies[i]->GetPosDt()); }
        std::cout << "],\"acceleration\":[";
        for (int i = 0; i < n; ++i) { if (i) std::cout << ','; WriteVector(bodies[i]->GetPosDt2()); }
        std::cout << "],\"reaction\":[";
        for (int i = 0; i < m; ++i) {
            if (i) std::cout << ',';
            WriteVector(links[i]->GetFrame2Abs().TransformDirectionLocalToParent(links[i]->GetReaction2().force));
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
