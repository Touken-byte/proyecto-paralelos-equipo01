#include <stdio.h>
#include <mpi.h>
int main(int argc,char**argv){
  MPI_Init(&argc,&argv);
  int r,s; char h[64]; int l;
  MPI_Comm_rank(MPI_COMM_WORLD,&r); MPI_Comm_size(MPI_COMM_WORLD,&s);
  MPI_Get_processor_name(h,&l);
  printf("MPI OK: rank %d de %d en %s\n",r,s,h);
  MPI_Finalize(); return 0;
}
