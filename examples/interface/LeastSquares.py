#
#  Copyright (c) 2009-2014, Jack Poulson
#  All rights reserved.
#
#  This file is part of Elemental and is under the BSD 2-Clause License, 
#  which can be found in the LICENSE file in the root directory, or at 
#  http://opensource.org/licenses/BSD-2-Clause
#
import El

n0 = n1 = 20

def LaplacianPlusIdentity(xSize,ySize):
  A = El.DistSparseMatrix()
  A.Resize(2*xSize*ySize,xSize*ySize)
  firstLocalRow = A.FirstLocalRow()
  localHeight = A.LocalHeight()
  A.Reserve(5*localHeight)
  hxInvSq = (1.*(xSize+1))**2
  hyInvSq = (1.*(ySize+1))**2
  for iLoc in xrange(localHeight):
    s = firstLocalRow + iLoc
    if s < xSize*ySize:
      x = s % xSize
      y = s / xSize
      A.QueueUpdate( s, s, 2*(hxInvSq+hyInvSq) )
      if x != 0:       A.QueueUpdate( s, s-1,     -hxInvSq )
      if x != xSize-1: A.QueueUpdate( s, s+1,     -hxInvSq )
      if y != 0:       A.QueueUpdate( s, s-xSize, -hyInvSq )
      if y != ySize-1: A.QueueUpdate( s, s+xSize, -hyInvSq )
    else:
      A.QueueUpdate( s, s-xSize*ySize, 1 )

  A.MakeConsistent()
  return A

# TODO: Extend sparse Multiply to support adjoints so this is not necessary
def LaplacianPlusIdentityAdjoint(xSize,ySize):
  A = El.DistSparseMatrix()
  A.Resize(xSize*ySize,2*xSize*ySize)
  firstLocalRow = A.FirstLocalRow()
  localHeight = A.LocalHeight()
  A.Reserve(6*localHeight)
  hxInvSq = (1.*(xSize+1))**2
  hyInvSq = (1.*(ySize+1))**2
  for iLoc in xrange(localHeight):
    s = firstLocalRow + iLoc
    x = s % xSize
    y = s / xSize
    A.QueueUpdate( s, s, 2*(hxInvSq+hyInvSq) )
    if x != 0:       A.QueueUpdate( s, s-1,     -hxInvSq )
    if x != xSize-1: A.QueueUpdate( s, s+1,     -hxInvSq )
    if y != 0:       A.QueueUpdate( s, s-xSize, -hyInvSq )
    if y != ySize-1: A.QueueUpdate( s, s+xSize, -hyInvSq )

    A.QueueUpdate( s, s+xSize*ySize, 1 )

  A.MakeConsistent()
  return A

A = LaplacianPlusIdentity(n0,n1)
AAdj = LaplacianPlusIdentityAdjoint(n0,n1)
El.Display( A, "A" )
El.Display( AAdj, "A^H" )
El.Display( A.DistGraph(), "Graph of A" )

C = El.DistSparseMatrix()
C.Resize( n0*n1, n0*n1 )
El.Syrk( El.LOWER, El.ADJOINT, 1, A, 0, C ) # NOTE: 'LOWER' does not do anything
El.Display( C, "A^H A" )
El.Display( C.DistGraph(), "Graph of A^H A" )

y = El.DistMultiVec()
El.Uniform( y, 2*n0*n1, 1 )
x = El.DistMultiVec()
El.Zeros( x, n0*n1, 1 )
El.SparseMultiply( 1, AAdj, y, 0, x )
El.Display( y, "y" )
El.Display( x, "A^H y" )

El.SymmetricSolveSparse(C,x)

yNrm = El.Nrm2(y)
rank = El.mpi.WorldRank()
if rank == 0:
  print "|| y ||_2 =", yNrm

xNrm = El.Nrm2(x)
if rank == 0:
  print "|| x ||_2 =", xNrm

El.SparseMultiply(-1.,A,x,1.,y)
El.Display( y, "A x - y" )
eNrm = El.Nrm2(y)
if rank == 0:
  print "|| A x - y ||_2 / || y ||_2 =", eNrm/yNrm

# Require the user to press a button before the figures are closed
commSize = El.mpi.Size( El.mpi.COMM_WORLD() )
El.Finalize()
if commSize == 1:
  raw_input('Press Enter to exit')
