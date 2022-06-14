//
// This file is released under the terms of the NASA Open Source Agreement (NOSA)
// version 1.3 as detailed in the LICENSE file which accompanies this software.
//

//////////////////////////////////////////////////////////////////////
// Face.h
// J.R. Gloudemans
//////////////////////////////////////////////////////////////////////

#if !defined(FACE_FACE__INCLUDED_)
#define FACE_FACE__INCLUDED_

#include "Defines.h"
#include "Vec2d.h"
#include "Vec3d.h"

#define _USE_MATH_DEFINES
#include <cmath>
#include <cassert>

#include <list>
#include <vector>
#include <set>
#include <map>
#include <algorithm>
using namespace std;

class Face;
class Edge;
class Surf;

//////////////////////////////////////////////////////////////////////
class Node
{
public:
    Node()
    {
        fixed = m_DeleteMeFlag = false;
        id = 0;
    }
    Node( const vec3d& p, const vec2d& uw_in )
    {
        pnt = p;
        uw = uw_in;
        fixed = m_DeleteMeFlag = false;
        id = 0;
    }
    virtual ~Node();

    list< Node* >::iterator list_ptr;

    bool m_DeleteMeFlag;

    vec3d pnt;              // Position
    vec2d uw;               // Parametric
    bool fixed;             // Dont move or delete
    int  id;

    vector< Edge* >  edgeVec;       // All Edges Which Use This Node

    void GetConnectNodes( vector< Node* > & cnVec );
    void GetConnectFaces( vector< Face* > & ctVec );

    void AddConnectEdge( Edge* e );
    void RemoveConnectEdge( Edge* e );
    void LaplacianSmooth();
    void LaplacianSmoothUW();
//  void AngleSmooth();
    void OptSmooth();

    bool AllInteriorConnectedFaces();

    void LaplacianSmooth( Surf* surfPtr );
    void AreaWeightedLaplacianSmooth( Surf* surfPtr );

};


//////////////////////////////////////////////////////////////////////
class Edge
{
public:
    Edge()
    {
        n0 = n1 = NULL;
        f0 = f1 = NULL;
        ridge = border = debugFlag = m_DeleteMeFlag = false;
        target_len = 0;
        m_Length = 0;
    }
    Edge( Node* node0, Node* node1 )
    {
        n0 = node0;
        n1 = node1;
        f0 = f1 = NULL;
        ridge = border = debugFlag = m_DeleteMeFlag = false;
        target_len = 0;
        m_Length = 0;
    }
    virtual ~Edge()                         {}

    list< Edge* >::iterator list_ptr;

    bool m_DeleteMeFlag;

    Node* n0;
    Node* n1;

    Face* f0;
    Face* f1;

    bool ridge;             // Dont Remove but Can Split
    bool border;            // Dont remove or split

    bool debugFlag;         // Flag for testing

    double target_len;
    double m_Length;

    Face* OtherFace( Face* t );
    Node* OtherNode( Node* n );
    void ReplaceNode( Node* curr_node, Node* replace_node );

    bool SetFace( Face* t );
    bool ContainsNodes( Node* in0, Node* in1 );


    double length()
    {
        return dist( n0->pnt, n1->pnt );
    }

    double ComputeLength()
    {
        m_Length = length();
        return m_Length;
    }
    double GetLength()
    {
        return m_Length;
    }

    bool BothAdjoiningTrisInterior();
    void ReplaceFace( Face* t, Face* replace_t );



};

//////////////////////////////////////////////////////////////////////
class Face
{
public:
    Face();
    Face( Node* nn0, Node* nn1, Node* nn2, Edge* ee0, Edge* ee1, Edge* ee2 );
    virtual ~Face();

    list< Face* >::iterator list_ptr;
    bool m_DeleteMeFlag;

    Node* n0;
    Node* n1;
    Node* n2;

    Edge* e0;
    Edge* e1;
    Edge* e2;

    void ComputeCosAngles( double* ang0, double* ang1, double* ang2 );
    static void ComputeCosAngles( Node* nn0, Node* nn1, Node* nn2, double* ang0, double* ang1, double* ang2 );

    void SetNodesEdges( Node* nn0, Node* nn1, Node* nn2, Edge* ee0, Edge* ee1, Edge* ee2 );

    Edge* FindEdge( Node* nn0, Node* nn1 );
    Edge* FindEdgeWithout( Node* node_ptr );
    Edge* FindLongEdge();

    void ReplaceNode( Node* curr_node, Node* replace_node );
    void ReplaceEdge( Edge* curr_edge, Edge* replace_edge );

    double ComputeQual();
    static double ComputeQual( Node* nn0, Node* nn1, Node* nn2 );

    double ComputeCosSmallAng();

    Node* OtherNode( Node* a, Node* b );

    bool Contains( Node* a, Node* b );
    bool Contains( Edge* e );
    double Area();

    vec3d Normal();
    static vec3d Normal( Node* n0, Node* n1, Node* n2 );

    bool CorrectOrder( Node* n0, Node* n1 );

    vec3d ComputeCenterPnt( Surf* surfPtr );

    bool debugFlag;

    // true if inside surface with a cid corresponding to an index.
    vector< bool > insideSurf;

    vector< int > insideCount;

    // Set to true if tri should be removed
    bool deleteFlag;

    void LoadAdjFaces( int num_levels, set< Face* > & triSet );

    unsigned char rgb[3];

protected:

};


class SimpTri
{
public:
    int ind0;
    int ind1;
    int ind2;
    vector<int> m_Tags;
};

#endif
