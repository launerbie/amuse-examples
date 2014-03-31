#!/usr/bin/env python
# -*- coding: utf-8 -*-

import h5py
import numpy

from amuse.units import constants, core

def semimajoraxis_from_binary(binary, G=constants.G):
    """ Calculates the semimajoraxis of a binary system. """

    if len(binary) != 2:
        raise Exception("Expects binary")

    else:
        total_mass = binary.mass.sum()
        position = binary[1].position - binary[0].position
        velocity = binary[1].velocity - binary[0].velocity

    specific_energy = (1.0/2.0)*velocity.lengths_squared() - G*total_mass/position.lengths()
    semimajor_axis = -G*total_mass/(2.0*specific_energy)
    return semimajor_axis

def eccentricity_from_binary(binary, G=constants.G):
    """ Calculates the eccentricity of a binary system. """
    if len(binary) != 2:
        raise Exception("Expects binary")

    else:
        total_mass = binary.mass.sum()
        position = binary[1].position - binary[0].position
        velocity = binary[1].velocity - binary[0].velocity

    specific_energy = (1.0/2.0)*velocity.lengths_squared() - G*total_mass/position.lengths()

    specific_angular_momentum = position.cross(velocity)
    eccentricity_argument = 2*specific_angular_momentum.lengths()**2 * specific_energy/(G**2*total_mass**2)
    if (eccentricity_argument <= -1): 
        eccentricity = 0.0
    else: 
        eccentricity = numpy.sqrt(1.0 + eccentricity_argument)
    return eccentricity

def orbital_elements(binary, G=constants.G, reference_direction=None, 
                     angle='degrees'):
    """ 
    Calculates the orbital elements of a binary system. 

    In this function, variables ending with an underscore indicate
    that they are vectors.

    energy := specific orbital energy or vis-viva energy, as it is defined
              at http://en.wikipedia.org/wiki/Specific_orbital_energy

    r_  :=  [rx, ry, rz]                     (relative position vector) 
    v_  :=  [vx, vy, vz]                     (relative velocity vector)
    h_  :=  r_ cross v_                     (specific angular momentum)
    mu  :=  G*binary.mass.sum()      (standard gravitational parameter)
    e_  :=  (v_ cross h_)/mu - r_/r               (eccentricity vector)
    n_  :=  k_ cross h_         (vector pointing towardsascending node)


    Parameters
    ----------
    binary : amuse.datamodel.particles.Particles instance
    G: Gravitational Constant
    reference_direction: shape (3,) array.


    Returns
    -------
    The orbital elements: a, e, i, w, W, f, which stand for:

    a: semi-major axis
    e: eccentricity
    i: inclination
    w: argument of periapsis
    W: longitude of ascending node
    f: true anomomaly

    """
    if len(binary) != 2:
        raise Exception("Expects binary")

    if angle not in ['degrees', 'radians']:
        raise Exception("invalid argument for angle keyword")

    #TODO: calculate from arbitrary reference direction
    # this means redefining n_ = k_ cross h_ ?
    if reference_direction is None:
        reference_direction = numpy.array([1, 0, 0])
    
    r_ = binary[1].position - binary[0].position
    v_ = binary[1].velocity - binary[0].velocity
    r = r_.length()
    v = v_.length()

    mu = G*binary.mass.sum()
    energy = 0.5*v**2 - mu/r

    ###########  specific angular momentum  ##############
    h_ = r_.cross(v_)
    h = h_.length() 

    ########  semimajoraxis a and eccentricity e  ########
    a = -mu/(2*energy)
    e_ = v_.cross(h_)/mu - r_/r 
    e = numpy.linalg.norm(e_) 
    #e = numpy.sqrt(1 + 2*energy*(h/mu)**2)

    ###################  inclination i  ##################
    i = numpy.arccos(h_.z/h)


    #################  ascending node n_  ################
    n_ = -1*h_.cross([0,0,1]) 
    n = n_.length()


    ##########  longtitude of ascending node W  ##########
    if n.number == 0:
        n_ = reference_direction
        W = 0
    else:
        if n_[1].number >= 0:
            W = numpy.arccos(n_[0]/n)
        else:
            W = 2*numpy.pi * numpy.arccos(n_[0]/n)


    ##############  argument of periapsis w  #############
    # Note that n_ is not unitless by definition
    if e > 0:
        if i == 0:# => place w at ascending node n
            w = 0
        else:
            #FIXME: possible error here. Tests with inclined orbits are not passing
            w = numpy.arccos((n_.dot(e_)/(n*e)))
            if e_[2] < 0: 
                w = 2*numpy.pi - w
    else: #circular orbit => place w at ascending node n
        w = 0 


    ##################  true anomaly f  ###################
    if e > 0:
        f = numpy.arccos(r_.dot(e_)/(e*r))
        if r_.dot(v_).number < 0:
            f = 2*numpy.pi - f
    elif e == 0:
        f = 0


    if angle == 'degrees':
        #print("e_:{}  n_:{}  h_:{} ".format(e_, n_, h_))
        return a, e, numpy.degrees(i), numpy.degrees(w), numpy.degrees(W),\
               numpy.degrees(f)
    elif angle == 'radians':
        return a, e, i, w, W, f


def quantify_dset(dset):
    if 'unit' in dset.attrs:
        unit = retrieve_unit(dset.attrs['unit'])
        return dset.value | unit

def retrieve_unit(reference_string):
    return eval(reference_string, core.__dict__)

def printshape(name, obj):
    if isinstance(obj, h5py.Dataset):
        print(name, obj.shape)

def printunit(name, obj):
    if isinstance(obj, h5py.Dataset):
        if 'unit' in obj.attrs:
            print(name, obj.attrs['unit'])


