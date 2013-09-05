"""
A unit testing module for coordinate system rotation.

Functions/methods tested:
  coordinate_rotation.adjust_lon_range  
  coordinate_rotation.rotation_matrix
  coordinate_rotation.rotate_spherical
  coordinate_rotation.switch_regular_axes

"""

import unittest

from math import pi, sqrt
import numpy

import os
import sys

module_dir = os.path.join(os.environ['HOME'], 'modules')
sys.path.insert(0, module_dir)
import coordinate_rotation as rot

module_dir2 = os.path.join(os.environ['HOME'], 'visualisation')
sys.path.insert(0, module_dir2)
import plot_map

import cdms2

import pdb


##########################
## unittest test clases ##
##########################

class testLonAdjust(unittest.TestCase):
    """Test class for testing the adjustment of longitude values."""

    def setUp(self):
        """Define the test data."""        

        self.data_degrees = numpy.array([0., 360., 378., 60., -30., -810.])
        self.data_radians = numpy.array([0., 2*pi, 2.1*pi, pi/3., -pi/6., -4.5*pi])


    def test_degrees_start0(self):
        """Test for data in degrees, start point = 0.0 [test for success]"""
        
        result = rot.adjust_lon_range(self.data_degrees, radians=False, start=0.0)
        answer = [0.0, 0.0, 18.0, 60.0, 330.0, 270.0] 
        numpy.testing.assert_array_equal(result, answer)


    def test_degrees_start180(self):
        """Test for data in degrees, start point = -180 [test for success]"""

        result = rot.adjust_lon_range(self.data_degrees, radians=False, start=-180.0)
        answer = [0., 0., 18., 60., -30., -90.] 
        numpy.testing.assert_array_equal(result, answer)	
    
    
    def test_radians_start0(self):
        """Test for data in radians, start point = 0.0 [test for success]"""

        result = rot.adjust_lon_range(self.data_radians, start=0.0)
        answer = [0., 0., 0.1*pi, pi/3., (11./6.)*pi, 1.5*pi] 
        numpy.testing.assert_array_equal(result, answer)        
        
        
    def test_radians_start180(self):
        """Test for data in radians, start point = -pi [test for success]"""

        result = rot.adjust_lon_range(self.data_radians, start=-pi)
        answer = [0., 0., 0.1*pi, pi/3., -pi/6., -0.5*pi] 
        numpy.testing.assert_array_equal(result, answer)	        


class testTransformationMatrix(unittest.TestCase):
    """Test class for the transformation matrix used
    in coordinate system rotations."""

    def setUp(self):
        """Define the sets of Euler angles (phi, theta, psi) to be tested"""

        self.angles = [[0.0, 0.0, 0.0],
                       [2 * pi, 2 * pi, 2 * pi],
                       [pi, pi, pi],
                       [0.0, 0.5 * pi, 0.3*pi],
                       [0.4 * pi, 1.2 * pi, 1.7 * pi]]

                        
    def test_no_rotation(self):
        """Test no rotation for psi = theta = psi = 0.0 [test for success]"""

        for phi, theta, psi in self.angles[0:2]:
            for inv in [True, False]:
                result = rot.rotation_matrix(phi, theta, psi, inverse=inv)
                numpy.testing.assert_allclose(result, numpy.identity(3), rtol=1e-07, atol=1e-07)
                

    def test_known_value(self):
        """Test the rotation matrix for a known answer (derived by hand) [test for success]"""
        
        phi, theta, psi = [pi/4., pi/3., pi/6.]
        result = rot.rotation_matrix(phi, theta, psi, inverse=False)
        
        a = sqrt(3.0) / 2
        b = 0.5
        c = 1 / sqrt(2.0)
        answer = numpy.empty([3,3])
        answer[0, 0] = (a * c) - (b * c * b)
        answer[0, 1] = (a * c) + (b * c * b)
        answer[0, 2] = b * a
        answer[1, 0] = -(b * c) - (b * c * a)
        answer[1, 1] = -(b * c) + (b * c * a)
        answer[1, 2] = a * a
        answer[2, 0] = a * c
        answer[2, 1] = -(a * c)
        answer[2, 2] = b

        numpy.testing.assert_allclose(result, answer, rtol=1e-07, atol=1e-07) 


    def test_known_inverse(self):
        """Test the inverse rotation matrix for a known answer (derived by hand) [test for success]"""
        
        phi, theta, psi = [pi / 4, pi / 3, pi / 6]
        result = rot.rotation_matrix(phi, theta, psi, inverse=True)
        
        a = sqrt(3.0) / 2
        b = 0.5
        c = 1 / sqrt(2.0)
        answer = numpy.empty([3,3])
        answer[0, 0] = (a * c) - (b * c * b)
        answer[0, 1] = -(b * c) - (b * c * a)
        answer[0, 2] = a * c
        answer[1, 0] = (a * c) + (b * c * b)
        answer[1, 1] = -(b * c) + (b * c * a)
        answer[1, 2] = -(a * c)
        answer[2, 0] = a * b
        answer[2, 1] = a * a
        answer[2, 2] = b

        numpy.testing.assert_allclose(result, answer, rtol=1e-07, atol=1e-07) 


    def test_invalid_input(self):
        """Test input angles outside of [0, 2*pi] [test for failure]"""

        self.assertRaises(AssertionError, rot.rotation_matrix, 0.0, pi, 6.5)


    def test_identity(self):
        """The transformation matrix, multiplied by its inverse, 
        should return the identity matrix [test for sanity]"""

        for phi, theta, psi in self.angles:
            A = rot.rotation_matrix(phi, theta, psi, inverse=False)
            Ainv = rot.rotation_matrix(phi, theta, psi, inverse=True)
            product = numpy.dot(A, Ainv)

            numpy.testing.assert_allclose(product, numpy.identity(3), rtol=1e-07, atol=1e-07)


class testRotateSpherical(unittest.TestCase):
    """Test class for rotations in spherical coordinates.
    
    I'm pretty sure rotate_spherical does not do lat=90 things properly.
    THIS NEEDS TO BE TESTED. If it doesn't, it may be a matter of altering the
    code so that lat=90 points are by default just allocated the coordinates of the
    new north pole.
    
    """

    def test_zero_rotation(self):
        """[test for success]"""
    
        phi, theta, psi = 0.0, 0.0, 0.0
        lats = [35, 35, 35, 35, -35, -35, -35, -35]
        lons = [55, 150, 234, 340, 55, 150, 234, 340]

        latsrot, lonsrot = rot.rotate_spherical(lats, lons, phi, theta, psi, invert=False)
	
        numpy.testing.assert_allclose(latsrot, lats, rtol=1e-03, atol=1e-03)
        numpy.testing.assert_allclose(lonsrot, lons, rtol=1e-03, atol=1e-03)

    
    def test_pure_phi(self):
        """Test pure rotations about the original z-axis (phi).
        For z-axis rotations, the simpliest place to test is the
        equator, as the specified rotation angle will correspond
        exactly to the change in longitude.
        
        Negative phi values correspond to a positive longitudinal 
        direction.
        
	    """
	
        phi = -50
        lats = numpy.array([0, 0, 0, 0, 0])
        lons = numpy.array([0, 65, 170, 230, 340])
        lons_answer = numpy.array([50, 115, 220, 280, 30])
	
        latsrot, lonsrot = rot.rotate_spherical(lats, lons, phi, 0, 0, invert=False)
        
        numpy.testing.assert_allclose(lats, latsrot, rtol=1e-07, atol=1e-07)
        numpy.testing.assert_allclose(lons_answer, lonsrot, rtol=1e-03, atol=1e-03)


    def test_pure_theta(self):
        """Test pure rotations about the original x-axis (theta).
        
        For x-axis rotations, the simpliest place to test is the
        90/270 longitude circle, as the specified rotation angle 
        will correspond exactly to the change in latitude (to visualise
        the rotations, draw a vertical crossection of that circle).
	
        """

        theta = 60
        lats = numpy.array([70, 70, 40, -32, -45, -80])
        lons = numpy.array([90, 270, -90, 90, -90, 90])
        lats_answer = numpy.array([10, 50, 80, -88, 15, -40])
        lons_answer = numpy.array([90, 90, 90, 270, 270, 270])
		
        latsrot, lonsrot = rot.rotate_spherical(lats, lons, 0, theta, 0, invert=False)
        
        numpy.testing.assert_allclose(lats_answer, latsrot, rtol=1e-03, atol=1e-03)
        numpy.testing.assert_allclose(lons_answer, lonsrot, rtol=1e-03, atol=1e-03)
	

    def test_pure_psi(self):
        """Test pure rotations about the final z-axis (psi)."""

        pass


class testNorthPoleToAngles(unittest.TestCase):
    """Test class for converting a new north pole position to the
    corresponding Euler angles."""

    def test_no_change(self):
        """Test for no change in north pole location [test for success]"""

        result = rot.north_pole_to_rotation_angles(90, 0)
        numpy.testing.assert_array_equal(result, numpy.zeros(1))


    def test_pure_meridional(self):
        """Test for a north pole change purely in the meridional direction"""

        r1 = rot.north_pole_to_rotation_angles(70, 0)
        r2 = rot.north_pole_to_rotation_angles(-60, 0)
        r3 = rot.north_pole_to_rotation_angles(-90, 0)
        results = [r1, r2, r3]

        a1 = [0, 20, 0]
        a2 = [0, 150, 0]
        a3 = [0, 180, 0]
        answers = [a1, a2, a3]

        for i in range(0,3):
            numpy.testing.assert_allclose(results[i], answers[i], rtol=1e-03, atol=1e-03)


class testSwitchAxes(self):
    """Test the complete switch of axes"""

    def test_np_0N_180E(self):
        """Test for new north pole at 0N, 180E [test for success].
        (corresponds to a swap of the lat and lon coordinates of each point?)

        """
        
        pass


    def test_np_90S_0E(self):
        """Test for new north pole at 90S, 0E [test for success].
        (corresponds to change in sign of latitude values)

        """
        
        pass


##############
## plotting ##
##############        

def create_latlon_dataset(res=2.5):
    """Create a dataset corresponding to the latitude (output 1) and
    longitude (output 2) of each grid point"""

    nlats = int((180.0 / res) + 1)
    nlons = int(360.0 / res)
    grid = cdms2.createUniformGrid(-90.0, nlats, res, 0.0, nlons, res)
    
    lat_data = numpy.zeros([nlats, nlons])
    lat_axis = numpy.arange(-90, 90 + res, res)
    for index in range(0, len(lats)):
        lat_data[index, :] = lats[index]
    lat_data_cdms = cdms2.createVariable(lat_data[:], grid=grid)

    lon_data = numpy.zeros([nlats, nlons])
    lon_axis1 = numpy.arange(0, 180 + res, res)
	lon_axis2 = numpy.arange(180 - res, 0, -res)
	for index in range(0, len(lon_axis1)):
	    lon_data[:, index] = lon_axis1[index]
    for index in range(0, len(lon_axis2)):
	    lon_data[:, index + len(lon_axis1)] = lon_axis2[index]
    lon_data_cdms = cdms2.createVariable(lon_data[:], grid=grid)

    return lat_data_cdms, lon_data_cdms


def switch_and_restore(data, new_np):
    """Test the switch_axes function"""

    lat_axis = data.getLatitude()
    lon_axis = data.getLongitude()
    
    rotated_data = rot.switch_regular_axes(data, lat_axis[:], lon_axis[:], new_np, invert=False)
    cdms_rotated_data = cdms2.createVariable(rotated_data[:], axes=[lat_axis, lon_axis])

    returned_data = calc_envelope.switch_regular_axes(rotated_data, lat_axis[:], lon_axis[:], new_np, invert=True)
    cdms_returned_data = cdms2.createVariable(returned_data[:], axes=[lat_axis, lon_axis])

    return cdms_rotated_data, cdms_returned_data
    

def plot_axis_switch(new_np):
    """Plot the original, rotated and returned data"""

    orig_lat_data, orig_lon_data = create_latlon_dataset()
    rotated_lat_data, returned_lat_data = switch_and_restore(orig_lat_data, new_np)
    rotated_lon_data, returned_lon_data = switch_and_restore(orig_lon_data, new_np)

    title = 'Axis switch for new NP at %sN, %sE' %(str(new_np[0]), str(new_np[1])) 

    # Latitude plot
    plot_lat_list = [original_lat_data, rotated_lat_data, returned_lat_data]
    plot_map.multiplot(plot_lat_list,
                       dimensions=(3, 1),  
                       title=title,
                       ofile='axis_switch_lat_%sN_%sE.png' %(str(new_np[0]), str(new_np[1])), 
                       row_headings=['original', 'rotated', 'returned'],
                       draw_axis=True, delat=15, delon=30, equator=True)

    # Longitude plot


if __name__ == '__main__':
    
    unittest.main()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", type=float, nargs=2, default=None, metavar=('LAT', 'LON'), 
                        help="latitude and longitude of new north pole for plot [default: 30N, 270E]")
    args = parser.parse_args()
    if args.plot:
        plot_axis_switch(args.plot)