#include <dolfinx/mesh/utils.h>
#include <dolfinx/geometry/utils.h>
#include <dolfinx/fem/CoordinateElement.h>
#include <dolfinx/common/MPI.h>
#include <mpi.h>
#include <iostream>
#include <iomanip>
#include <optional>
#include <span>

// Invoke the original four-argument API on the genuine old baseline. Once the
// implementation provides the requested option, call its five-argument API.
// This compatibility dispatch never changes the returned geometric decision.
template<typename Mesh>
auto own(const Mesh& mesh, std::span<const double> points, double padding, bool closest)
{
  if constexpr (requires { dolfinx::geometry::determine_point_ownership(mesh, points, padding, std::nullopt, closest); })
    return dolfinx::geometry::determine_point_ownership(mesh, points, padding, std::nullopt, closest);
  else
    return dolfinx::geometry::determine_point_ownership(mesh, points, padding, std::nullopt);
}
int main(int argc, char** argv)
{
  MPI_Init(&argc,&argv);
  {
    using namespace dolfinx;
    const std::vector<std::int64_t> cells{0,1,2,3};
    const std::vector<double> coordinates{0,0,0,1,0,0,0,1,0,0,0,1};
    const std::vector<double> points{.1,.1,.1,.5,.5,.5,1.1,1.1,1.1};
    fem::CoordinateElement<double> coordinate_element(mesh::CellType::tetrahedron,1);
    auto mesh=mesh::create_mesh(MPI_COMM_WORLD,std::span<const std::int64_t>(cells),coordinate_element,
      coordinates,std::array<std::size_t,2>{4,3},mesh::GhostMode::none);
    for (bool closest: {false,true})
    {
      auto result=own(mesh,std::span<const double>(points),0.,closest);
      std::cout<<"closest="<<closest<<" owners=";
      for (int owner:result.src_owner)std::cout<<owner<<',';
      std::cout<<" cells=";
      for (auto cell:result.dest_cells)std::cout<<mesh.topology()->original_cell_index.front()[cell]<<',';
      std::cout<<'\n';
    }
  }
  MPI_Finalize();
}
