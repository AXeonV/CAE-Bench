#include <dolfinx/mesh/utils.h>
#include <dolfinx/geometry/utils.h>
#include <dolfinx/fem/CoordinateElement.h>
#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <spdlog/spdlog.h>
#include <mpi.h>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <optional>
#include <span>
#include <stdexcept>
#include <vector>

template<typename Mesh>
auto ownership(const Mesh& mesh, std::span<const double> points, double padding, int mode)
{
  if(mode==2)
    return dolfinx::geometry::determine_point_ownership(mesh,points,padding,std::nullopt);
  if constexpr(requires { dolfinx::geometry::determine_point_ownership(mesh,points,padding,std::nullopt,bool{}); })
    return dolfinx::geometry::determine_point_ownership(mesh,points,padding,std::nullopt,mode==1);
  else
    return dolfinx::geometry::determine_point_ownership(mesh,points,padding,std::nullopt);
}

int main(int argc,char** argv)
{
  MPI_Init(&argc,&argv);
  int exit_code=0;
  try
  {
    spdlog::set_level(spdlog::level::off);
    namespace pt=boost::property_tree;
    pt::ptree input;pt::read_json(std::cin,input);
    const int dimension=input.get<int>("dimension");
    std::vector<double> vertices,queries;
    std::vector<std::int64_t> cells,labels;
    for(const auto& row:input.get_child("vertices"))
      for(const auto& value:row.second)vertices.push_back(value.second.get_value<double>());
    for(const auto& row:input.get_child("queries"))
    {
      std::size_t count=0;
      for(const auto& value:row.second){queries.push_back(value.second.get_value<double>());++count;}
      for(;count<3;++count)queries.push_back(0.);
    }
    for(const auto& row:input.get_child("cells"))
      for(const auto& value:row.second)cells.push_back(value.second.get_value<std::int64_t>());
    for(const auto& row:input.get_child("cell_ids"))labels.push_back(row.second.get_value<std::int64_t>());
    const auto celltype=dimension==2?dolfinx::mesh::CellType::triangle:dolfinx::mesh::CellType::tetrahedron;
    dolfinx::fem::CoordinateElement<double> element(celltype,1);
    auto mesh=dolfinx::mesh::create_mesh(MPI_COMM_WORLD,std::span<const std::int64_t>(cells),element,
      vertices,std::array<std::size_t,2>{vertices.size()/dimension,static_cast<std::size_t>(dimension)},dolfinx::mesh::GhostMode::none);
    const auto result=ownership(mesh,std::span<const double>(queries),input.get<double>("padding"),input.get<int>("mode"));
    const auto vectors=dolfinx::geometry::shortest_vector(mesh,dimension,
      std::span<const std::int32_t>(result.dest_cells),std::span<const double>(result.dest_points));
    const std::size_t count=queries.size()/3;
    std::vector<std::int64_t> assigned(count,-1);
    std::vector<double> distances(count,-1.);
    for(std::size_t p=0;p<result.dest_cells.size();++p)
    {
      std::size_t q=0;
      for(;q<count;++q)
        if(queries[3*q]==result.dest_points[3*p] && queries[3*q+1]==result.dest_points[3*p+1]
            && queries[3*q+2]==result.dest_points[3*p+2])break;
      if(q==count)throw std::runtime_error("Returned point has no input identity");
      const auto original=mesh.topology()->original_cell_index.front().at(result.dest_cells[p]);
      assigned[q]=labels.at(original);
      distances[q]=std::sqrt(vectors[3*p]*vectors[3*p]+vectors[3*p+1]*vectors[3*p+1]+vectors[3*p+2]*vectors[3*p+2]);
    }
    std::cout<<std::setprecision(17)<<'[';
    for(std::size_t q=0;q<count;++q)
    {
      if(q)std::cout<<',';
      std::cout<<"{\"owned\":"<<(result.src_owner.at(q)>=0?1:0)<<",\"cell_id\":"<<assigned[q]<<",\"distance\":"<<distances[q]<<'}';
    }
    std::cout<<"]\n";
  }
  catch(const std::exception& error){std::cerr<<error.what()<<'\n';exit_code=2;}
  MPI_Finalize();
  return exit_code;
}
