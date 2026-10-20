package com.example.javabackend.mapper;

import com.example.javabackend.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface UserMapper {
    User findByUsername(String username);
    User findByEmail(String email);
    User findById(Long id);
    List<User> findAll();
    int insert(User user);
    int update(User user);
    int updateLastLogin(@Param("id") Long id);
    int incrementLearningCount(@Param("id") Long id);
    int incrementXp(@Param("id") Long id, @Param("amount") int amount);
    List<User> findTopByXp(@Param("limit") int limit);
    List<User> findTopByStudyTime(@Param("limit") int limit);
}
