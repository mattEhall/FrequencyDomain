import pytest
import sys
import numpy as np
import yaml
import matplotlib.pyplot as plt

# test local code; consider src layout in future to test installed code
sys.path.append('..')
sys.path.append('c:/code/MoorPy')
import FrequencyDomain as fd
import MoorPy as mp


#import Capytaine_placeholder as capy


import importlib
mp = importlib.reload(mp)
fd = importlib.reload(fd)



def runRAFT(fname_design, fname_env):
    '''
    This the main function for running the RAFT model in standalone form, where inputs are contained in the specified input files.
    '''
    
    
    with open('OC3spar.yaml') as file:
        design = yaml.load(file, Loader=yaml.FullLoader)
    
    print("Loading file: "+fname_design)
    print(f"'{design['name']}'")
    
    # ----- process turbine information -----------------------------------------
    # No processing actually needed yet - we pass the dictionary directly to RAFT.
    
    
    # ----- process platform information ----------------------------------------
    
    # create member strings (4 different input formats supported)
    # note: some redundancy here with Member.init - may want to reconsider
    
    if design['platform']['member_input_type'] == 'strings':
        
        memberStrings = design['platform']['member_strings']
    
    
    elif design['platform']['member_input_type'] == 'arrays':
        
        mi = design['platform']['member_arrays']
        
        nMembers = len(mi['number'])
    
        memberStrings = []      # initialize an empty list to hold all the member strings
        
        for i in range(nMembers):
        
            memberStrings.append( f"{mi['number'   ][i]} "
                                  f"{mi['type'     ][i]} "
                                  f"{mi['shape'    ][i]} "
                                  f"{mi['dA'       ][i]} "
                                  f"{mi['dB'       ][i]} "
                                  f"{mi['xa'       ][i]} "
                                  f"{mi['ya'       ][i]} "
                                  f"{mi['za'       ][i]} "
                                  f"{mi['xb'       ][i]} "
                                  f"{mi['yb'       ][i]} "
                                  f"{mi['zb'       ][i]} "
                                  f"{mi['tA'       ][i]} "
                                  f"{mi['tB'       ][i]} "
                                  f"{mi['l_fill'   ][i]} "
                                  f"{mi['rho_fill' ][i]} "
                                  f"{mi['rho_shell'][i]}")
    
    
    elif design['platform']['member_input_type'] == 'list':
        
        memberStrings = []      # initialize an empty list to hold all the member strings
        
        for mi in design['platform']['member_list']:
        
            memberStrings.append( f"{mi['number'   ]} "
                                  f"{mi['type'     ]} "
                                  f"{mi['shape'    ]} "
                                  f"{mi['dA'       ]} "
                                  f"{mi['dB'       ]} "
                                  f"{mi['xa'       ]} "
                                  f"{mi['ya'       ]} "
                                  f"{mi['za'       ]} "
                                  f"{mi['xb'       ]} "
                                  f"{mi['yb'       ]} "
                                  f"{mi['zb'       ]} "
                                  f"{mi['tA'       ]} "
                                  f"{mi['tB'       ]} "
                                  f"{mi['l_fill'   ]} "
                                  f"{mi['rho_fill' ]} "
                                  f"{mi['rho_shell']}")
    
    
    elif design['platform']['member_input_type'] == 'file':
    
        fname_members = design['platform']['member_file']
        
        with open(fnam_members) as file: 
            lines = file.read()
    
        memberStrings = lines[1:]    # take the member strings to be all lines in the file after the first one
    
    else:
        raise ValueError("YAML input entry for platform:member_input_type ('"+design['platform']['member_input_type']+"') not supported.")
    
    
    # ----- process mooring information ----------------------------------------------
      
    MooringSystem = mp.System()
    
    MooringSystem.parseYAML(design['mooring'])
      
    MooringSystem.initialize()
    
    
    
    # may want to check that mooring depth matches wave environment depth at some point <<<      
            
    depth = float(design['mooring']['water_depth'])
            
    
    
    

    # --- BEM ---
    # (preprocessing step:) Generate and load BEM hydro data
    capyData = []
    
    capyTestFile = f'./test_data/mesh_converge_0.750_1.250.nc'

    w = np.arange(0.05, 2.8, 0.05)  # frequency range (to be set by modeling options yaml)
    
    '''
    # load or generate Capytaine data
    if capyDataExists:
        wDes, addedMass, damping, fEx = capy.read_capy_nc(capyTestFile, wDes=w)
    else:
        wCapy, addedMass, damping, fEx = capy.call_capy(meshFName, w)
        
    # package results to send to model
    capyData = (wCapy, addedMass, damping, fEx)
    '''

    
    # --- Create Model ---
    # now that memberStrings and MooringSystem are made on way or another, call the model 

    model = fd.Model(memberList=memberStrings, ms=MooringSystem, w=w, depth=depth, BEM=capyData, RNAprops=design['turbine'])  # set up model

    model.setEnv(Hs=8, Tp=12, V=10, Fthrust=float(design['turbine']['Fthrust']))  # set basic wave and wind info

    model.calcSystemProps()          # get all the setup calculations done within the model

    model.solveEigen()

    model.calcMooringAndOffsets()    # calculate the offsets for the given loading
    
    model.solveDynamics()            # put everything together and iteratively solve the dynamic response
    
    model.plot()
    
    plt.show()
    
    return model
    
    
    
def runRAFTfromWEIS():    
    ''' this is the more realistic case where we have to process wt_opt to produce memberStrings and MooringSystem <<<<<<<'''
        
    # Members
    floating_init_options = modeling_options['floating']  # I need to include these because this is where we get name_member
    n_members = floating_init_options['members']['n_members'] 
    
    n_joints = len(wt_opt['floating.floating_joints.location'])
    rA = np.zeros([n_joints, 2])
    rB = np.zeros([n_joints, 2])
    for i in range(n_joints):
        joint_locs[i,:] = wt_opt['floating.floating_joints.location'][i,:]
    
    for i in range(n_members):
        name_member = floating_init_options['members']['name'][i]
        type = 2 # arbitrary value to designate that the member is part of the floating substructure
        
        dA = wt_opt['floating.floating_member_' + name_member + '.outer_diameter'][0]
        dB = wt_opt['floating.floating_member_' + name_member + '.outer_diameter'][1]
        # <<<<<<<< the IEA ontology paper says that the outer_diameter parameter describes two diameters at joints 1 and 2
        
        t = sum(wt_opt['floating.floating_member_' + name_member + '.layer_thickness'])
        # took the sum of this because we just want to know the total thickness to get to dB
        # <<<<<<<<< not sure if I summed it right because the thickness of each layer is [j,:] in gc_WT_InitModel
        
        if n_joints != n_members + 1:
            raise ValueError('There should be n_members+1 number of joints to use the right rA and rB values')
        rA = joint_locs[i,:]
        rB = joint_locs[i+1,:]
        
        # <<<<<<<<<<< Ballast section: PROBABLY WON'T WORK. JUST USING WHAT I WAS GIVEN
        v_fill = wt_opt['floating.floating_member_' + name_member + '.ballast_volume'] 
        rho_fill = wt_opt['floating.floating_member_' + name_member + '.ballast_material.rho']

        #dB_fill = (dBi-dAi)*(self.l_fill/self.l) + dAi       # interpolated diameter of member where the ballast is filled to
        #v_fill = (np.pi/4)*(1/3)*(dAi**2+dB_fill**2+dAi*dB_fill)*self.l_fill    #[m^3]
        # There's a way to solve for l_fill using the above equations given v_fill
        
        # Going to simplify and just take it as the proportion of length to volume
        dAi = dA - 2*t # assming the thickness is constant along the member with respect to the length
        dBi = dB - 2*t
        l = np.linalg.norm(rB-rA)
        v_mem = (np.pi/4)*(1/3)*(dAi**2+dBi**2+dAi*dBi)*l
        
        l_fill = l * v_fill/v_mem
        
        # plug variables into a Member in FrequencyDomain and append to the memberString list
                    # change to string in FD v
        memberStrings.append(fd.Member( str(name_member)+" "+str(type)+" "+str(dA)+" "+str(dB)+" "+str(rA[0])+" "+str(rA[1])+" "+str(rA[2])+\
                                 " "+str(rB[0])+" "+str(rB[1])+" "+str(rB[2])+" "+str(t)+" "+str(l_fill)+" "+str(rho_fill), nw))
  
  
    
    # Create a MoorPy system
    ms = mp.System()
    ms.depth = wt_opt['env.water_depth']
    
    # Add the line types that are provided in the wt_opt OpenMDAO object
    n_line_types = len(wt_opt['mooring.line_diameter'])
    for i in range(n_line_types):
        name = wt_opt['mooring.line_names'][i]
        d = wt_opt['mooring.line_diameter'][i]
        massden = wt_opt['mooring.line_mass_density'][i]
        EA = wt_opt['mooring.line_stiffness'][i]
        MBL = wt_opt['mooring.line_breaking_load'][i]
        cost = wt_opt['mooring.line_cost'][i]
        
        ms.LineTypes[name] = mp.LineType( name, d, massden, EA, MBL=MBL, cost=cost, notes="made in FrequencyDomain.py" )
        
    # Add the wind turbine platform reference point   <<<<<<<<<<<<<< Get values
    ms.addBody(0, PRP, m=mTOT, v=VTOT, rCG=rCG_TOT, AWP=AWP_TOT, rM=np.array([0,0,zMeta]), f6Ext=np.array([Fthrust,0,0, 0,Mthrust,0]))
    
    # Add points to the sytem
    for i in range(n_nodes):
        ID = wt_opt['mooring.node_id'][i]            # <<<<<<<<< not 100% on the syntax of these calls
        
        if wt_opt['mooring.node_type'][i] == 'fixed':
            type = 1
        elif wt_opt['mooring.node_type'][i] == 'vessel':
            type = -1
        elif wt_opt['mooring.node_type'][i] == 'connection':
            type = 0
        
        r = np.array( wt_opt['mooring.nodes_location'][i,:], dtype=float)
        # TODO - can add in other variables for the point like anchor ID, fairlead_type, node_mass, node_volume, drag area, added mass
        ms.PointList.append( mp.Point( ID, type, r ) )

        # attach body points to the body
        # the nodes_location array is relative to inertial frame if Fixed or Connect, but relative to platform frame if Vessel
        if type==-1:
            ms.BodyList[0].addPoint(ID, r)
        
    
    # Add and attach lines to the nodes of the system
    n_lines = len(wt_opt['mooring.unstretched_length'])
    for i in range(n_lines):
        ID = wt_opt['mooring.line_id'][i]
        LineLength = wt_opt['mooring.unstretched_length'][i]
        linetype = wt_opt['mooring.line_type'][i]
        
        ms.LineList.append( mp.Line( ID, LineLength, LineTypes[linetype] ) )
        
        node1 = wt_opt['mooring.node1_id']
        node2 = wt_opt['mooring.node2_id']
        # Run an if statement to make sure that node1 is the deeper point
        if ms.PointList[node1].r[2] < ms.PointList[node2].r[2]:
            pass
        elif ms.PointList[node1].r[2] > ms.PointList[node2].r[2]:
            node1 = node2
            node2 = node1
        else:
            pass # if the z value of both points is the same, then it doesn't matter
        
        ms.PointList[node1].addLine(ID, 0)
        ms.PointList[node2].addLine(ID, 1)
    
        # TODO - anchor types
        
        # Turn on the system
        ms.initialize()
        MooringSystem = ms

    # NEED TO ADD THE FINAL MODEL RUN STEPS HERE ONCE THE ABOVE WORKS

    

if __name__ == "__main__":
    
    model = runRAFT('OC3spar.yaml', 'env.yaml')
    
    
    fowt = model.fowtList[0]
    print('Tower Mass:          ',np.round(fowt.mtower,2),' kg')
    print('Tower CG:            ',np.round(fowt.rCG_tow[2],4),' m from SWL')
    print('Substructure Mass:   ',np.round(fowt.msubstruc,2),' kg')
    print('Substructure CG:     ',np.round(fowt.rCG_sub[2],4),' m from SWL')
    print('Steel Mass:          ',np.round(fowt.mshell,2),' kg')
    print('Ballast Mass:        ',np.round(fowt.mballast,2),' kg')
    print('Ballast Densities    ',fowt.pb,' kg/m^3')
    print('Total Mass:          ',np.round(fowt.M_struc[0,0],2),' kg')
    print('Total CG:            ',np.round(fowt.rCG_TOT[2],2),' m from SWL')
    print('Roll Inertia at PCM  ',np.round(fowt.I44,2),' kg-m^2')
    print('Pitch Inertia at PCM ',np.round(fowt.I55,2),' kg-m^2')
    print('Yaw Inertia at PCM   ',np.round(fowt.I66,2),' kg-m^2')
    print('Roll Inertia at PRP: ',np.round(fowt.I44B,2),' kg-m^2')
    print('Pitch Inertia at PRP:',np.round(fowt.I55B,2),' kg-m^2')
    print('Buoyancy (pgV):      ',np.round(fowt.V*fowt.env.g*fowt.env.rho,2),' N')
    print('Center of Buoyancy:  ',np.round(fowt.rCB[2],4),'m from SWL')
    print('C33:                 ',np.round(fowt.C_hydro[2,2],2),' N')
    print('C44:                 ',np.round(fowt.C_hydro[3,3],2),' Nm/rad')
    print('C55:                 ',np.round(fowt.C_hydro[4,4],2),' Nm/rad')
    print('F_lines: ',list(np.round(np.array(model.F_moor0),2)),' N')
    print('C_lines: ',model.C_moor0)
    
    def pdiff(x,y):
        return (abs(x-y)/y)*100
    
    
    
    
    